# 百度主动推送：把 URL 推给百度，比等它自己抓快得多
#
# 用法：站点上线或改版后运行
#   powershell -ExecutionPolicy Bypass -File .\scripts\baidu-push.ps1
#
# URL 默认从 sitemap.xml 读取，新增页面只要进了 sitemap 就会自动带上；
# 也可以用 -Urls 手动指定：
#   .\scripts\baidu-push.ps1 -Urls 'https://ipowerbi.icu/','https://ipowerbi.icu/xxx/'
#
# token 不提交到仓库：脚本优先读环境变量 BAIDU_PUSH_TOKEN，
# 其次读项目根目录的 .baidu-token（已在 .gitignore 里）。

param([string[]]$Urls)

$site = 'https://ipowerbi.icu'
$root = Split-Path $PSScriptRoot -Parent
$tokenFile = Join-Path $root '.baidu-token'

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
    $Urls = @([regex]::Matches($sm.Content, '<loc>(https?://[^<]+)</loc>') |
              ForEach-Object { $_.Groups[1].Value })
  } catch {
    Write-Host "读取 sitemap 失败：$($_.Exception.Message)"
    exit 1
  }
}

if (-not $Urls -or $Urls.Count -eq 0) {
  Write-Host '没有可推送的 URL：sitemap.xml 里没有 <loc> 条目'
  exit 1
}

Write-Host "准备推送 $($Urls.Count) 个 URL："
$Urls | ForEach-Object { Write-Host "  $_" }

$uri = "http://data.zz.baidu.com/urls?site=$site&token=$token"
$tmp = [System.IO.Path]::GetTempFileName()

try {
  [System.IO.File]::WriteAllLines($tmp, $Urls, (New-Object System.Text.UTF8Encoding($false)))

  # 百度接口是 http，走本机代理经常失败，这里强制直连
  $result = & curl.exe -s --noproxy '*' --max-time 30 -X POST `
                       --data-binary "@$tmp" -H 'Content-Type: text/plain' $uri

  if (-not $result) {
    Write-Host '推送失败：没有返回内容，检查网络或 token'
    exit 1
  }

  Write-Host "百度推送返回：$result"
} finally {
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}
