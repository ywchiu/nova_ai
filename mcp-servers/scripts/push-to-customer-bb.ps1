$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  推送到客戶內部 BitBucket Data Center             ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 確認在正確的目錄
$rootDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $rootDir
Write-Host "  專案目錄: $rootDir"
Write-Host ""

# 詢問客戶 BitBucket URL
$BB_URL = Read-Host "  客戶 BitBucket Repo URL (例如 http://bitbucket.company.com/scm/NOVA/nova-ai-mcp.git)"

if ([string]::IsNullOrWhiteSpace($BB_URL)) {
    Write-Host "  [錯誤] URL 不可為空" -ForegroundColor Red
    exit 1
}

# 確認 git
$gitExists = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitExists) {
    Write-Host "  [錯誤] 找不到 git，請先安裝 Git for Windows" -ForegroundColor Red
    exit 1
}

# 檢查是否已有 git repo
if (-not (Test-Path ".git")) {
    Write-Host "  初始化 git repo..." -ForegroundColor Yellow
    git init
    git add -A
    git commit -m "Nova AI MCP Servers - 課程教材"
}

# 加上 customer remote
git remote remove customer 2>$null
git remote add customer $BB_URL
Write-Host ""
Write-Host "  推送到 $BB_URL ..." -ForegroundColor Yellow
Write-Host "  (可能會要求輸入客戶 BitBucket 的帳號密碼)" -ForegroundColor DarkGray
Write-Host ""

git push customer main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "  ═══════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  推送成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "  學員 clone 指令：" -ForegroundColor Green
    Write-Host "    git clone $BB_URL" -ForegroundColor Cyan
    Write-Host "    cd nova-ai-mcp\mcp-servers" -ForegroundColor Cyan
    Write-Host "    powershell -ExecutionPolicy Bypass -File scripts\install.ps1" -ForegroundColor Cyan
    Write-Host "  ═══════════════════════════════════════════" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  [失敗] 推送失敗" -ForegroundColor Red
    Write-Host "  請確認：" -ForegroundColor Yellow
    Write-Host "    1. URL 是否正確" -ForegroundColor Yellow
    Write-Host "    2. 帳號是否有 push 權限" -ForegroundColor Yellow
    Write-Host "    3. Repo 是否已在 BitBucket 建好" -ForegroundColor Yellow
}
