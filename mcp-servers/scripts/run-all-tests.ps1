# ══════════════════════════════════════════════════════════════════════════════
# Nova MCP Servers — 全部測試腳本
#
# 用法：在 mcp-servers 目錄下執行
#   powershell -ExecutionPolicy Bypass -File scripts\run-all-tests.ps1
# ══════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 取得 mcp-servers 根目錄 ──────────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   Nova MCP Servers — 全部測試            ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Push-Location $RootDir
try {

    # ── Step 1：確認 pytest 已安裝 ──────────────────────────────────────────
    Write-Host "=== 確認 pytest ===" -ForegroundColor Yellow
    try {
        & python -m pytest --version 2>&1 | Out-Null
        Write-Host "  [OK] pytest 已安裝" -ForegroundColor Green
    } catch {
        Write-Host "  安裝 pytest..." -ForegroundColor Gray
        & python -m pip install pytest pytest-asyncio -q 2>&1 | Out-Null
        Write-Host "  [OK] pytest 安裝完成" -ForegroundColor Green
    }

    # ── 定義測試套件 ────────────────────────────────────────────────────────
    $testSuites = @(
        @{
            Name = "Jira MCP"
            Files = @(
                "jira_mcp\test_server.py",
                "jira_mcp\test_demo_issue_driven.py",
                "jira_mcp\test_demo_report.py"
            )
        },
        @{
            Name = "BitBucket MCP"
            Files = @(
                "bitbucket_mcp\test_demo_review.py"
            )
        },
        @{
            Name = "Jenkins MCP"
            Files = @(
                "jenkins_mcp\test_server.py",
                "jenkins_mcp\test_pipeline.py",
                "jenkins_mcp\test_demo_cicd.py"
            )
        },
        @{
            Name = "Integration"
            Files = @(
                "test_integration.py"
            )
        }
    )

    $totalPassed = 0
    $totalFailed = 0
    $totalSkipped = 0
    $suiteResults = @()

    # ── 依序跑每個測試套件 ──────────────────────────────────────────────────
    foreach ($suite in $testSuites) {
        Write-Host ""
        Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
        Write-Host "  $($suite.Name) 測試" -ForegroundColor Cyan
        Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan

        $suitePassed = 0
        $suiteFailed = 0
        $suiteSkipped = 0
        $suiteStatus = "OK"

        foreach ($file in $suite.Files) {
            if (-not (Test-Path $file)) {
                Write-Host "  [SKIP] $file（檔案不存在）" -ForegroundColor Gray
                continue
            }

            Write-Host ""
            Write-Host "  --- $file ---" -ForegroundColor White
            $output = & python -m pytest $file -v --tb=short 2>&1
            $outputStr = $output -join "`n"

            # 輸出測試結果
            foreach ($line in $output) {
                $lineStr = "$line"
                if ($lineStr -match "PASSED") {
                    Write-Host "  $lineStr" -ForegroundColor Green
                } elseif ($lineStr -match "FAILED") {
                    Write-Host "  $lineStr" -ForegroundColor Red
                } elseif ($lineStr -match "SKIPPED|SKIP") {
                    Write-Host "  $lineStr" -ForegroundColor Yellow
                } elseif ($lineStr -match "ERROR") {
                    Write-Host "  $lineStr" -ForegroundColor Red
                } else {
                    Write-Host "  $lineStr" -ForegroundColor Gray
                }
            }

            # 解析結果
            if ($outputStr -match "(\d+) passed") { $suitePassed += [int]$Matches[1] }
            if ($outputStr -match "(\d+) failed") { $suiteFailed += [int]$Matches[1]; $suiteStatus = "FAIL" }
            if ($outputStr -match "(\d+) skipped") { $suiteSkipped += [int]$Matches[1] }
            if ($outputStr -match "(\d+) error") { $suiteFailed += [int]$Matches[1]; $suiteStatus = "FAIL" }
        }

        $totalPassed += $suitePassed
        $totalFailed += $suiteFailed
        $totalSkipped += $suiteSkipped

        $suiteResults += @{
            Name    = $suite.Name
            Passed  = $suitePassed
            Failed  = $suiteFailed
            Skipped = $suiteSkipped
            Status  = $suiteStatus
        }
    }

    # ── 顯示總結 ────────────────────────────────────────────────────────────
    Write-Host ""
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║   測試總結                                              ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    $format = "  {0,-18} {1,-8} {2,-8} {3,-8} {4}"
    Write-Host ($format -f "測試套件", "通過", "失敗", "跳過", "狀態") -ForegroundColor White
    Write-Host "  ──────────────────────────────────────────────────────────"

    foreach ($r in $suiteResults) {
        $statusStr = "[$($r.Status)]"
        $color = if ($r.Status -eq "OK") { "Green" } else { "Red" }
        Write-Host ($format -f $r.Name, $r.Passed, $r.Failed, $r.Skipped, $statusStr) -ForegroundColor $color
    }

    Write-Host "  ──────────────────────────────────────────────────────────"

    $totalAll = $totalPassed + $totalFailed + $totalSkipped
    $summaryColor = if ($totalFailed -eq 0) { "Green" } else { "Red" }
    Write-Host ($format -f "合計", $totalPassed, $totalFailed, $totalSkipped, "") -ForegroundColor $summaryColor

    Write-Host ""
    if ($totalFailed -eq 0) {
        Write-Host "  全部通過！共 $totalPassed 個測試" -ForegroundColor Green
    } else {
        Write-Host "  有 $totalFailed 個測試失敗，請檢查上方輸出" -ForegroundColor Red
    }
    Write-Host ""

} finally {
    Pop-Location
}
