# 百度主动推送：把 URL 推给百度，比等它自己抓快得多
#
# 百度普通收录 API 每天只有约 10 条配额，所以这个脚本默认只推「首页 + 最近 7 天有更新的页面」，
# 按片提交；配额用完就停，超配额的批次会自动拆成单条重试，尽量把剩下的额度用干净。
#
# 用法：
#   .\scripts\baidu-push.ps1                    # 默认：首页 + 最近 7 天更新过的页面
#   .\scripts\baidu-push.ps1 -Days 2            # 只看最近 2 天
#   .\scripts\baidu-push.ps1 -Urls 'https://ipowerbi.icu/'   # 只推指定 URL（改版后最常用）
#   .\scripts\baidu-push.ps1 -All               # 全量推 sitemap（会超配额，通常不需要）
#   .\scripts\baidu-push.ps1 -DryRun            # 只打印计划，不发请求
#
# 日常新增文章不用跑这个脚本：公众号工作流的 push_search.py 会按天自动推新文章。
# token 优先读环境变量 BAIDU_PUSH_TOKEN，其次读项目根目录的 .baidu-token。

param(
  [string[]]$Urls,
  [switch]$All,
  [int]$Days = 7,
  [int]$Max = 5,
  [switch]$DryRun
)

# Windows PowerShell 5.1 默认按本地代码页输出，中文会变问号
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$site = 'https://ipowerbi.icu'
$root = Split-Path $PSScriptRoot -Parent
$tokenFile = Join-Path $root '.baidu-token'

if ($Max -lt 1) { $Max = 1 }
if ($Max -gt 10) { $Max = 10 }   # 百度单次提交上限 10 条

$token = $env:BAIDU_PUSH_TOKEN
if (-not $token -and (Test-Path $tokenFile)) {
  $token = (Get-Content $tokenFile -Raw).Trim()
}
if (-not $token) {
  Write-Host '缺少 token：设置环境变量 BAIDU_PUSH_TOKEN，或在项目根目录创建 .baidu-token 文件'
  exit 1
}

if (-not $Urls) {
  try {
    $sm = Invoke-WebRequest -Uri "$site/sitemap.xml" -UseBasicParsing -TimeoutSec 20
  } catch {
    Write-Host "读取 sitemap 失败：$($_.Exception.Message)"
    exit 1
  }

  # 逐条解析 <url> 块，拿到 loc 和 lastmod
  $entries = @()
  foreach ($block in [regex]::Matches($sm.Content, '(?s)<url>(.*?)</url>')) {
    $loc = [regex]::Match($block.Value, '<loc>([^<]+)</loc>')
    if (-not $loc.Success) { continue }
    $lastmod = [regex]::Match($block.Value, '<lastmod>([^<]+)</lastmod>')
    $entries += [pscustomobject]@{
      Url     = $loc.Groups[1].Value.Trim()
      LastMod = if ($lastmod.Success) { $lastmod.Groups[1].Value.Trim() } else { '' }
    }
  }

  if ($All) {
    Write-Host '注意：-All 会全量推送 sitemap，超过每日配额的部分会被百度拒绝。'
    $Urls = @($entries | ForEach-Object { $_.Url })
  } else {
    $cutoff = (Get-Date).AddDays(-$Days).ToString('yyyy-MM-dd')
    $homeUrl = "$site/"
    $Urls = @($entries |
      Where-Object { $_.Url -eq $homeUrl -or ($_.LastMod -and $_.LastMod -ge $cutoff) } |
      ForEach-Object { $_.Url })
    Write-Host "按「首页 + 最近 $Days 天更新（$cutoff 起）」筛选：$($Urls.Count) / $($entries.Count) 个 URL"
  }
}

if (-not $Urls -or $Urls.Count -eq 0) {
  Write-Host '没有需要推送的 URL：最近没有页面更新。新增文章交给每日工作流即可。'
  exit 0
}

Write-Host "准备推送 $($Urls.Count) 个 URL："
$Urls | ForEach-Object { Write-Host "  $_" }

if ($DryRun) {
  Write-Host '（DryRun：未发送任何请求）'
  exit 0
}

$uri = "http://data.zz.baidu.com/urls?site=$site&token=$token"
$sent = 0
$remain = $null
$quotaHit = $false

# 发一批；返回 curl 的原始 JSON 文本
function Invoke-BaiduPush([string[]]$chunk) {
  # 直接传正文，不落临时文件：临时目录路径常含中文，curl 的 @file 读不了
  $body = ($chunk -join "`n")
  # 百度接口是 http，走本机代理经常失败，这里强制直连
  return (& curl.exe -s --noproxy '*' --max-time 30 -X POST `
                     --data-binary $body -H 'Content-Type: text/plain' $uri)
}

for ($i = 0; $i -lt $Urls.Count; $i += $Max) {
  $end = [Math]::Min($i + $Max - 1, $Urls.Count - 1)
  $chunk = @($Urls[$i..$end])
  $result = Invoke-BaiduPush $chunk

  if (-not $result) {
    Write-Host '推送失败：没有返回内容，检查网络或 token'
    break
  }

  Write-Host "百度返回：$result"

  if ($result -match 'over quota') {
    if ($chunk.Count -eq 1) {
      $quotaHit = $true
      break
    }
    # 整批被拒时拆成单条重试，把剩余额度用掉
    Write-Host "这一批（$($chunk.Count) 条）超出剩余配额，改为逐条推送……"
    foreach ($one in $chunk) {
      $single = Invoke-BaiduPush @($one)
      Write-Host "  $one -> $single"
      if (-not $single -or $single -match 'over quota' -or $single -match '"error"') {
        $quotaHit = $true
        break
      }
      $sent += 1
      $m1 = [regex]::Match($single, '"remain"\s*:\s*(\d+)')
      if ($m1.Success) {
        $remain = [int]$m1.Groups[1].Value
        if ($remain -le 0) { $quotaHit = $true; break }
      }
    }
    if ($quotaHit) { break }
    continue
  }

  if ($result -match '"error"') {
    Write-Host '百度返回错误，本次推送中止。'
    break
  }

  $sent += $chunk.Count
  $m = [regex]::Match($result, '"remain"\s*:\s*(\d+)')
  if ($m.Success) {
    $remain = [int]$m.Groups[1].Value
    if ($remain -le 0) {
      Write-Host '今日配额已用完。'
      break
    }
  }
}

$left = $Urls.Count - $sent
if ($left -le 0) {
  $tail = if ($remain -ne $null) { "今日剩余配额约 $remain 条。" } else { '' }
  Write-Host "完成：本次提交 $sent 条，全部成功。$tail"
} else {
  Write-Host "结果：已提交 $sent 条，剩余 $left 条未推（今日配额用完，明天会自动补）。"
}
