# ══════════════════════════════════════════════════════════════════════════════
# Nova MCP Servers — 一鍵安裝腳本
#
# 用法：在 mcp-servers 目錄下執行
#   powershell -ExecutionPolicy Bypass -File scripts\install.ps1
# ══════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 取得 mcp-servers 根目錄 ──────────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   Nova MCP Servers — 一鍵安裝            ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Push-Location $RootDir
try {

    # ── Step 1：檢查 Python ──────────────────────────────────────────────────
    Write-Host "=== Step 1：檢查 Python ===" -ForegroundColor Yellow
    try {
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                Write-Host "  [OK] $pythonVersion" -ForegroundColor Green
            } else {
                Write-Host "  [警告] Python 版本太舊（$pythonVersion），建議 3.10 以上" -ForegroundColor Red
                Write-Host "  請安裝 Python 3.10+：https://www.python.org/downloads/" -ForegroundColor Red
                Write-Host "  如果有 USB 離線安裝包，請執行 usb_package\python-3.11.9-amd64.exe" -ForegroundColor Yellow
                exit 1
            }
        }
    } catch {
        Write-Host "  [錯誤] 找不到 Python！" -ForegroundColor Red
        Write-Host "  請先安裝 Python 3.10+：https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "  安裝時務必勾選「Add Python to PATH」" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  如果有 USB 離線安裝包，請執行：" -ForegroundColor Yellow
        Write-Host "    usb_package\python-3.11.9-amd64.exe" -ForegroundColor White
        exit 1
    }

    # ── Step 2：安裝 pip 套件 ────────────────────────────────────────────────
    Write-Host ""
    Write-Host "=== Step 2：安裝 Python 套件 ===" -ForegroundColor Yellow

    $pipSuccess = $false

    # 先嘗試線上安裝
    Write-Host "  嘗試線上安裝..." -ForegroundColor Gray
    try {
        & python -m pip install -r requirements.txt -q 2>&1 | Out-Null
        $pipSuccess = $true
        Write-Host "  [OK] 線上安裝成功" -ForegroundColor Green
    } catch {
        Write-Host "  [提示] 線上安裝失敗，嘗試離線安裝..." -ForegroundColor Yellow
    }

    # 線上失敗，嘗試離線安裝（packages-win 目錄）
    if (-not $pipSuccess) {
        $offlinePaths = @(
            (Join-Path $RootDir "packages-win"),
            (Join-Path (Split-Path -Parent $RootDir) "usb_package\packages-win")
        )

        foreach ($offlinePath in $offlinePaths) {
            if (Test-Path $offlinePath) {
                Write-Host "  找到離線套件目錄：$offlinePath" -ForegroundColor Gray
                try {
                    & python -m pip install --no-index --find-links="$offlinePath" -r requirements.txt -q 2>&1 | Out-Null
                    $pipSuccess = $true
                    Write-Host "  [OK] 離線安裝成功" -ForegroundColor Green
                    break
                } catch {
                    Write-Host "  [提示] 從 $offlinePath 離線安裝失敗" -ForegroundColor Yellow
                }
            }
        }
    }

    if (-not $pipSuccess) {
        Write-Host "  [錯誤] 套件安裝失敗！" -ForegroundColor Red
        Write-Host "  請確認：" -ForegroundColor Red
        Write-Host "    1. 網路是否正常（或有 proxy 需要設定）" -ForegroundColor Red
        Write-Host "    2. 離線套件目錄 packages-win\ 是否存在" -ForegroundColor Red
        Write-Host "  手動使用 proxy：" -ForegroundColor Yellow
        Write-Host "    pip install -r requirements.txt --proxy http://proxy:8080" -ForegroundColor White
        exit 1
    }

    # ── Step 3：驗證三個 server.py 語法 ──────────────────────────────────────
    Write-Host ""
    Write-Host "=== Step 3：驗證 MCP Server 語法 ===" -ForegroundColor Yellow

    $servers = @(
        @{ Name = "jira_mcp";      Path = "jira_mcp\server.py" },
        @{ Name = "bitbucket_mcp"; Path = "bitbucket_mcp\server.py" },
        @{ Name = "jenkins_mcp";   Path = "jenkins_mcp\server.py" }
    )

    $allSyntaxOk = $true
    foreach ($server in $servers) {
        $result = & python -m py_compile $server.Path 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $($server.Name)" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] $($server.Name) — $result" -ForegroundColor Red
            $allSyntaxOk = $false
        }
    }

    if (-not $allSyntaxOk) {
        Write-Host ""
        Write-Host "  [警告] 有語法錯誤，請檢查上方訊息" -ForegroundColor Red
        exit 1
    }

    # ── 完成 ────────────────────────────────────────────────────────────────
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "  ║   安裝完成！                              ║" -ForegroundColor Green
    Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  下一步：" -ForegroundColor Cyan
    Write-Host "    1. 執行 scripts\setup-env.ps1 設定認證資訊" -ForegroundColor White
    Write-Host "    2. 執行 scripts\test-connection.ps1 測試連線" -ForegroundColor White
    Write-Host ""

} finally {
    Pop-Location
}
