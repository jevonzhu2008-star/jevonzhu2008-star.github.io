# 部署后把 URL 主动推送给 Bing / Yandex（IndexNow 协议）
#
# 用法：站点推上 GitHub Pages 并上线后，在本目录运行
#   powershell -ExecutionPolicy Bypass -File .\scripts\indexnow.ps1
#
# 密钥文件 ca8fb82aa608eb6566678430c4a768a8.txt 必须在站点根目录，且可公开访问：
#   https://ipowerbi.icu/ca8fb82aa608eb6566678430c4a768a8.txt

param(
  [string[]]$Urls = @(
    'https://ipowerbi.icu/',
    'https://ipowerbi.icu/AIA-PowerBI-Portfolio/'
  )
)

$key = 'ca8fb82aa608eb6566678430c4a768a8'
$siteHost = 'ipowerbi.icu'

$payload = @{
  host        = $siteHost
  key         = $key
  keyLocation = "https://$siteHost/$key.txt"
  urlList     = $Urls
} | ConvertTo-Json -Depth 3

$body = [System.Text.Encoding]::UTF8.GetBytes($payload)

# 国内网络直连 api.indexnow.org 通常可用；若挂了代理，先清空当前会话的代理变量再试。
try {
  $res = Invoke-WebRequest -Uri 'https://api.indexnow.org/indexnow' `
                           -Method Post -Body $body `
                           -ContentType 'application/json; charset=utf-8' `
                           -UseBasicParsing
  Write-Host "IndexNow 已提交，HTTP $($res.StatusCode)（200 或 202 即成功）"
} catch {
  Write-Host "IndexNow 提交失败：$($_.Exception.Message)"
  Write-Host "检查密钥文件和站点是否已上线：https://$siteHost/$key.txt"
  exit 1
}
