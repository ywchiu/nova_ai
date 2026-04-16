# ══════════════════════════════════════════════════════════════════════════════
# Nova MCP Servers — 互動式 .env 設定腳本
#
# 用法：在 mcp-servers 目錄下執行
#   powershell -ExecutionPolicy Bypass -File scripts\setup-env.ps1
# ══════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 取得 mcp-servers 根目錄 ──────────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   Nova MCP Servers — 環境設定精靈        ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 選擇部署類型 ────────────────────────────────────────────────────────────
Write-Host "請選擇部署類型：" -ForegroundColor Yellow
Write-Host "  [1] Data Center（公司自建伺服器，使用 PAT）" -ForegroundColor White
Write-Host "  [2] Cloud（Atlassian Cloud / bitbucket.org，使用 Email + API Token）" -ForegroundColor White
Write-Host ""

do {
    $choice = Read-Host "請輸入 1 或 2"
} while ($choice -ne "1" -and $choice -ne "2")

$isCloud = ($choice -eq "2")
$envLines = @()

Write-Host ""
Write-Host "══════════════════════════════════════════" -ForegroundColor Gray

# ── Jira 設定 ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Jira 設定 ===" -ForegroundColor Yellow

if ($isCloud) {
    Write-Host "  Cloud 模式：需要 Email + API Token" -ForegroundColor Gray
    Write-Host "  取得 API Token：https://id.atlassian.com/manage-profile/security/api-tokens" -ForegroundColor Gray
    Write-Host ""

    $jiraUrl = Read-Host "  Jira URL（例如 https://your-site.atlassian.net）"
    $jiraEmail = Read-Host "  Jira Email"
    $jiraToken = Read-Host "  Jira API Token"

    $envLines += "# ── Jira（Cloud）──────────────────────────────"
    $envLines += "JIRA_BASE_URL=$jiraUrl"
    $envLines += "JIRA_EMAIL=$jiraEmail"
    if ($jiraToken -match "=") {
        $envLines += "JIRA_API_TOKEN=`"$jiraToken`""
    } else {
        $envLines += "JIRA_API_TOKEN=$jiraToken"
    }
} else {
    Write-Host "  Data Center 模式：需要 Personal Access Token (PAT)" -ForegroundColor Gray
    Write-Host "  取得 PAT：Jira -> Profile -> Personal Access Tokens -> Create token" -ForegroundColor Gray
    Write-Host ""

    $jiraUrl = Read-Host "  Jira URL（例如 http://jira.company.com）"
    $jiraPat = Read-Host "  Jira PAT"

    $envLines += "# ── Jira（Data Center）────────────────────────"
    $envLines += "JIRA_BASE_URL=$jiraUrl"
    if ($jiraPat -match "=") {
        $envLines += "JIRA_PAT=`"$jiraPat`""
    } else {
        $envLines += "JIRA_PAT=$jiraPat"
    }
}

# ── BitBucket 設定 ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== BitBucket 設定 ===" -ForegroundColor Yellow

if ($isCloud) {
    Write-Host "  Cloud 模式：需要 Username + API Token" -ForegroundColor Gray
    Write-Host "  取得 App Password：https://bitbucket.org/account/settings/app-passwords/" -ForegroundColor Gray
    Write-Host ""

    $bbUrl = Read-Host "  BitBucket API URL（預設 https://api.bitbucket.org/2.0，直接 Enter 使用預設）"
    if ([string]::IsNullOrWhiteSpace($bbUrl)) { $bbUrl = "https://api.bitbucket.org/2.0" }
    $bbUser = Read-Host "  BitBucket Username"
    $bbToken = Read-Host "  BitBucket API Token（App Password）"

    $envLines += ""
    $envLines += "# ── BitBucket（Cloud）─────────────────────────"
    $envLines += "BB_BASE_URL=$bbUrl"
    $envLines += "BB_USER=$bbUser"
    if ($bbToken -match "=") {
        $envLines += "BB_API_TOKEN=`"$bbToken`""
    } else {
        $envLines += "BB_API_TOKEN=$bbToken"
    }
} else {
    Write-Host "  Data Center 模式：需要 Personal Access Token (PAT)" -ForegroundColor Gray
    Write-Host "  取得 PAT：BitBucket -> Profile -> Manage Account -> HTTP Access Tokens" -ForegroundColor Gray
    Write-Host ""

    $bbUrl = Read-Host "  BitBucket URL（例如 http://bitbucket.company.com）"
    $bbPat = Read-Host "  BitBucket PAT"

    $envLines += ""
    $envLines += "# ── BitBucket（Data Center）───────────────────"
    $envLines += "BB_BASE_URL=$bbUrl"
    if ($bbPat -match "=") {
        $envLines += "BB_PAT=`"$bbPat`""
    } else {
        $envLines += "BB_PAT=$bbPat"
    }
}

# ── Jenkins 設定 ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Jenkins 設定 ===" -ForegroundColor Yellow
Write-Host "  Jenkins 使用 Username + API Token（Basic Auth）" -ForegroundColor Gray
Write-Host "  取得 API Token：Jenkins -> 右上角帳號 -> Configure -> API Token -> Add new Token" -ForegroundColor Gray
Write-Host ""

$jenkinsUrl = Read-Host "  Jenkins URL（例如 http://jenkins.company.com）"
$jenkinsUser = Read-Host "  Jenkins 帳號"
$jenkinsToken = Read-Host "  Jenkins API Token"

$envLines += ""
$envLines += "# ── Jenkins ──────────────────────────────────"
$envLines += "JENKINS_URL=$jenkinsUrl"
$envLines += "JENKINS_USER=$jenkinsUser"
if ($jenkinsToken -match "=") {
    $envLines += "JENKINS_API_TOKEN=`"$jenkinsToken`""
} else {
    $envLines += "JENKINS_API_TOKEN=$jenkinsToken"
}

# ── 寫入 .env ───────────────────────────────────────────────────────────────
$envPath = Join-Path $RootDir ".env"
$envContent = $envLines -join "`n"
[System.IO.File]::WriteAllText($envPath, $envContent, [System.Text.Encoding]::UTF8)

Write-Host ""
Write-Host "  [OK] .env 已建立：$envPath" -ForegroundColor Green

# ── 產生 Cline MCP Settings JSON ────────────────────────────────────────────
Write-Host ""
Write-Host "=== 產生 Cline MCP Settings ===" -ForegroundColor Yellow

$escapedRoot = $RootDir -replace '\\', '\\'

# 根據 Cloud / DC 產生不同的 env 區塊
if ($isCloud) {
    $jiraEnv = @"
        "JIRA_BASE_URL": "$($jiraUrl -replace '\\', '\\')",
        "JIRA_EMAIL": "$jiraEmail",
        "JIRA_API_TOKEN": "$jiraToken"
"@
    $bbEnv = @"
        "BB_BASE_URL": "$($bbUrl -replace '\\', '\\')",
        "BB_USER": "$bbUser",
        "BB_API_TOKEN": "$bbToken"
"@
} else {
    $jiraEnv = @"
        "JIRA_BASE_URL": "$($jiraUrl -replace '\\', '\\')",
        "JIRA_PAT": "$jiraPat"
"@
    $bbEnv = @"
        "BB_BASE_URL": "$($bbUrl -replace '\\', '\\')",
        "BB_PAT": "$bbPat"
"@
}

$clineJson = @"
{
  "mcpServers": {
    "jira": {
      "command": "python",
      "args": ["$escapedRoot\\jira_mcp\\server.py"],
      "env": {
$jiraEnv
      },
      "disabled": false,
      "alwaysAllow": []
    },
    "bitbucket": {
      "command": "python",
      "args": ["$escapedRoot\\bitbucket_mcp\\server.py"],
      "env": {
$bbEnv
      },
      "disabled": false,
      "alwaysAllow": []
    },
    "jenkins": {
      "command": "python",
      "args": ["$escapedRoot\\jenkins_mcp\\server.py"],
      "env": {
        "JENKINS_URL": "$($jenkinsUrl -replace '\\', '\\')",
        "JENKINS_USER": "$jenkinsUser",
        "JENKINS_API_TOKEN": "$jenkinsToken"
      },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
"@

$clineJsonPath = Join-Path $RootDir "my_cline_settings.json"
[System.IO.File]::WriteAllText($clineJsonPath, $clineJson, [System.Text.Encoding]::UTF8)

Write-Host "  [OK] Cline 設定已存到：$clineJsonPath" -ForegroundColor Green

# ── 完成 ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║   設定完成！                              ║" -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  下一步：" -ForegroundColor Cyan
Write-Host "    1. 執行 scripts\test-connection.ps1 測試連線" -ForegroundColor White
Write-Host "    2. 開啟 VSCode -> Ctrl+Shift+P -> Cline: Open MCP Settings" -ForegroundColor White
Write-Host "    3. 把 my_cline_settings.json 的內容貼入" -ForegroundColor White
Write-Host ""
Write-Host "  提示：Token 含 = 號時，.env 裡已自動加上雙引號" -ForegroundColor Gray
Write-Host ""
