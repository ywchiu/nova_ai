# ══════════════════════════════════════════════════════════════════════════════
# Nova MCP Servers — 連線測試腳本
#
# 用法：在 mcp-servers 目錄下執行
#   powershell -ExecutionPolicy Bypass -File scripts\test-connection.ps1
# ══════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 取得 mcp-servers 根目錄 ──────────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   Nova MCP Servers — 連線測試            ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Push-Location $RootDir
try {

    # 檢查 .env 是否存在
    if (-not (Test-Path ".env")) {
        Write-Host "  [錯誤] 找不到 .env 檔！請先執行 scripts\setup-env.ps1" -ForegroundColor Red
        exit 1
    }

    $results = @()

    # ── 測試 Jira ───────────────────────────────────────────────────────────
    Write-Host "測試 Jira 連線..." -ForegroundColor Yellow
    $jiraResult = "FAIL"
    $jiraDetail = ""
    try {
        $output = & python -c @"
import asyncio, sys
sys.path.insert(0, '.')
try:
    from jira_mcp.server import jira_list_projects
    result = asyncio.run(jira_list_projects())
    if 'error' in result.lower() or '錯誤' in result:
        print('FAIL:' + result[:100])
    else:
        print('OK')
except Exception as e:
    print('FAIL:' + str(e)[:100])
"@ 2>&1
        $outputStr = $output -join " "
        if ($outputStr.StartsWith("OK")) {
            $jiraResult = "OK"
            $jiraDetail = "jira_list_projects 成功"
        } else {
            $jiraDetail = $outputStr -replace "^FAIL:", ""
        }
    } catch {
        $jiraDetail = $_.Exception.Message
    }

    # ── 測試 BitBucket ──────────────────────────────────────────────────────
    Write-Host "測試 BitBucket 連線..." -ForegroundColor Yellow
    $bbResult = "FAIL"
    $bbDetail = ""
    try {
        $output = & python -c @"
import asyncio, sys
sys.path.insert(0, '.')
try:
    from bitbucket_mcp.server import bb_request, IS_CLOUD
    if IS_CLOUD:
        result = asyncio.run(bb_request('GET', '/repositories'))
    else:
        result = asyncio.run(bb_request('GET', '/projects'))
    print('OK')
except Exception as e:
    print('FAIL:' + str(e)[:100])
"@ 2>&1
        $outputStr = $output -join " "
        if ($outputStr.StartsWith("OK")) {
            $bbResult = "OK"
            $bbDetail = "bitbucket_list_repos 成功"
        } else {
            $bbDetail = $outputStr -replace "^FAIL:", ""
        }
    } catch {
        $bbDetail = $_.Exception.Message
    }

    # ── 測試 Jenkins ────────────────────────────────────────────────────────
    Write-Host "測試 Jenkins 連線..." -ForegroundColor Yellow
    $jenkinsResult = "FAIL"
    $jenkinsDetail = ""
    try {
        $output = & python -c @"
import asyncio, sys
sys.path.insert(0, '.')
try:
    from jenkins_mcp.server import jenkins_list_jobs, ListJobsInput
    result = asyncio.run(jenkins_list_jobs(ListJobsInput()))
    if 'error' in result.lower() or '錯誤' in result:
        print('FAIL:' + result[:100])
    else:
        print('OK')
except Exception as e:
    print('FAIL:' + str(e)[:100])
"@ 2>&1
        $outputStr = $output -join " "
        if ($outputStr.StartsWith("OK")) {
            $jenkinsResult = "OK"
            $jenkinsDetail = "jenkins_list_jobs 成功"
        } else {
            $jenkinsDetail = $outputStr -replace "^FAIL:", ""
        }
    } catch {
        $jenkinsDetail = $_.Exception.Message
    }

    # ── 顯示結果表格 ────────────────────────────────────────────────────────
    Write-Host ""
    Write-Host "  ══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  連線測試結果" -ForegroundColor Cyan
    Write-Host "  ══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""

    $format = "  {0,-15} {1,-8} {2}"
    Write-Host ($format -f "服務", "狀態", "說明") -ForegroundColor White
    Write-Host "  ──────────────────────────────────────────────────────────"

    # Jira
    $color = if ($jiraResult -eq "OK") { "Green" } else { "Red" }
    Write-Host ($format -f "Jira", "[$jiraResult]", $jiraDetail) -ForegroundColor $color

    # BitBucket
    $color = if ($bbResult -eq "OK") { "Green" } else { "Red" }
    Write-Host ($format -f "BitBucket", "[$bbResult]", $bbDetail) -ForegroundColor $color

    # Jenkins
    $color = if ($jenkinsResult -eq "OK") { "Green" } else { "Red" }
    Write-Host ($format -f "Jenkins", "[$jenkinsResult]", $jenkinsDetail) -ForegroundColor $color

    Write-Host "  ──────────────────────────────────────────────────────────"
    Write-Host ""

    # 總結
    $total = 3
    $passed = @($jiraResult, $bbResult, $jenkinsResult) | Where-Object { $_ -eq "OK" } | Measure-Object | Select-Object -ExpandProperty Count

    if ($passed -eq $total) {
        Write-Host "  全部通過！（$passed/$total）" -ForegroundColor Green
    } else {
        Write-Host "  通過 $passed/$total — 請檢查失敗項目" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  常見原因：" -ForegroundColor Gray
        Write-Host "    - .env 裡的 URL 或 Token 有誤" -ForegroundColor Gray
        Write-Host "    - 網路不通（VPN 未連線、防火牆阻擋）" -ForegroundColor Gray
        Write-Host "    - Token 含 = 號但沒用雙引號包起來" -ForegroundColor Gray
    }
    Write-Host ""

} finally {
    Pop-Location
}
