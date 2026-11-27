# 核验 Google Search Console 的 DNS TXT 验证记录是否生效
#
# 用法：
#   .\scripts\check-gsc-dns.ps1
#   .\scripts\check-gsc-dns.ps1 -Domain ipowerbi.icu -Expected 'google-site-verification=xxx'
#
# 先查系统 DNS；没命中会自动回退到 1.1.1.1 / 8.8.8.8 / 223.5.5.5，
# 避免本地路由器缓存滞后造成「明明加好了却查不到」。

param(
  [string]$Domain = 'ipowerbi.icu',
  [string]$Expected = 'google-site-verification=noqOr9B0Er0boI9uioShC9plRox-uNG0SNGUJwCmVo0'
)

try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Get-TxtRecords([string]$dnsServer) {
  $params = @{ Name = $Domain; Type = 'TXT'; ErrorAction = 'Stop'; DnsOnly = $true }
  if ($dnsServer) { $params.Server = $dnsServer }
  $records = Resolve-DnsName @params
  return @($records | Where-Object { $_.Strings } | ForEach-Object { $_.Strings -join '' })
}

$servers = @('', '1.1.1.1', '8.8.8.8', '223.5.5.5')
$found = $false
$anyTxt = @()

foreach ($s in $servers) {
  $label = if ($s) { $s } else { '系统默认' }
  try {
    $txt = Get-TxtRecords $s
  } catch {
    Write-Host "[$label] 查询失败：$($_.Exception.Message)"
    continue
  }
  if ($txt.Count -eq 0) {
    Write-Host "[$label] 无 TXT 记录"
    continue
  }
  foreach ($t in $txt) {
    Write-Host "[$label] $t"
    $anyTxt += $t
    if ($t -like "*$Expected*") { $found = $true }
  }
  if ($found) { break }
}

Write-Host ''
if ($found) {
  Write-Host '✔ 已找到 GSC 验证记录，可以回 Search Console 点「验证」了。'
  exit 0
} elseif ($anyTxt.Count -gt 0) {
  Write-Host '✘ 有 TXT 记录，但没有匹配到预期的 google-site-verification。'
  Write-Host "  期望包含：$Expected"
  exit 1
} else {
  Write-Host '✘ 所有 DNS 服务器都没查到 TXT 记录。'
  Write-Host "  期望包含：$Expected"
  exit 1
}
