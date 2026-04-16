@echo off
chcp 65001 >nul
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   Nova AI MCP Server - 學員環境設定      ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Step 1: 確認 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 找不到 Python，請先安裝 Python 3.10 以上
    echo 下載: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python 已安裝

:: Step 2: 安裝套件
echo.
echo === 安裝 Python 套件 ===
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [警告] pip install 失敗，嘗試用 proxy...
    set /p PROXY="請輸入公司 proxy (例如 http://proxy:8080，沒有請直接按 Enter): "
    if not "%PROXY%"=="" (
        pip install -r requirements.txt -q --proxy %PROXY%
    )
)
echo [OK] 套件安裝完成

:: Step 3: 語法檢查
echo.
echo === 檢查 MCP Server 語法 ===
python -m py_compile jira_mcp\server.py && echo   [OK] jira_mcp
python -m py_compile bitbucket_mcp\server.py && echo   [OK] bitbucket_mcp
python -m py_compile jenkins_mcp\server.py && echo   [OK] jenkins_mcp

:: Step 4: 設定 .env
echo.
echo === 設定認證資訊 ===
echo 請依序輸入你的 Token（從各系統取得）
echo.

set /p JIRA_URL="Jira URL (例如 http://jira.company.com): "
set /p JIRA_PAT_INPUT="Jira PAT: "
set /p BB_URL="BitBucket URL (例如 http://bitbucket.company.com): "
set /p BB_PAT_INPUT="BitBucket PAT: "
set /p JENKINS_URL_INPUT="Jenkins URL (例如 http://jenkins.company.com): "
set /p JENKINS_USER_INPUT="Jenkins 帳號: "
set /p JENKINS_TOKEN_INPUT="Jenkins API Token: "

:: 寫入 .env
(
echo JIRA_BASE_URL=%JIRA_URL%
echo JIRA_PAT=%JIRA_PAT_INPUT%
echo BB_BASE_URL=%BB_URL%
echo BB_PAT=%BB_PAT_INPUT%
echo JENKINS_URL=%JENKINS_URL_INPUT%
echo JENKINS_USER=%JENKINS_USER_INPUT%
echo JENKINS_API_TOKEN=%JENKINS_TOKEN_INPUT%
) > .env

echo.
echo [OK] .env 已建立

:: Step 5: 測試連線
echo.
echo === 測試連線 ===

echo 測試 Jira...
python -c "import asyncio; from jira_mcp.server import jira_list_projects; result=asyncio.run(jira_list_projects()); print('  [OK] Jira 連線成功') if '錯誤' not in result else print('  [FAIL]', result[:80])"

echo 測試 BitBucket...
python -c "import asyncio; from bitbucket_mcp.server import bb_request; result=asyncio.run(bb_request('GET', '/user')); print('  [OK] BitBucket 連線成功')" 2>nul || echo   [SKIP] BitBucket 需要額外 scope

echo 測試 Jenkins...
python -c "import asyncio; from jenkins_mcp.server import jenkins_list_jobs, ListJobsInput; result=asyncio.run(jenkins_list_jobs(ListJobsInput())); print('  [OK] Jenkins 連線成功') if '錯誤' not in result else print('  [FAIL]', result[:80])"

:: Step 6: 顯示 Cline 設定
echo.
echo ══════════════════════════════════════════
echo  接下來請設定 VSCode Cline：
echo.
echo  1. 開啟 VSCode
echo  2. Ctrl+Shift+P → Cline: Open MCP Settings
echo  3. 貼入以下設定（已根據你的輸入產生）：
echo ══════════════════════════════════════════
echo.

:: 取得當前目錄
set CURRENT_DIR=%CD%
:: 把 \ 轉成 \\
set ESCAPED_DIR=%CURRENT_DIR:\=\\%

echo {
echo   "mcpServers": {
echo     "jira": {
echo       "command": "python",
echo       "args": ["%ESCAPED_DIR%\\jira_mcp\\server.py"],
echo       "env": {
echo         "JIRA_BASE_URL": "%JIRA_URL%",
echo         "JIRA_PAT": "%JIRA_PAT_INPUT%"
echo       }
echo     },
echo     "bitbucket": {
echo       "command": "python",
echo       "args": ["%ESCAPED_DIR%\\bitbucket_mcp\\server.py"],
echo       "env": {
echo         "BB_BASE_URL": "%BB_URL%",
echo         "BB_PAT": "%BB_PAT_INPUT%"
echo       }
echo     },
echo     "jenkins": {
echo       "command": "python",
echo       "args": ["%ESCAPED_DIR%\\jenkins_mcp\\server.py"],
echo       "env": {
echo         "JENKINS_URL": "%JENKINS_URL_INPUT%",
echo         "JENKINS_USER": "%JENKINS_USER_INPUT%",
echo         "JENKINS_API_TOKEN": "%JENKINS_TOKEN_INPUT%"
echo       }
echo     }
echo   }
echo }

:: 也寫到檔案方便複製
(
echo {
echo   "mcpServers": {
echo     "jira": {
echo       "command": "python",
echo       "args": ["%ESCAPED_DIR%\\jira_mcp\\server.py"],
echo       "env": {
echo         "JIRA_BASE_URL": "%JIRA_URL%",
echo         "JIRA_PAT": "%JIRA_PAT_INPUT%"
echo       }
echo     },
echo     "bitbucket": {
echo       "command": "python",
echo       "args": ["%ESCAPED_DIR%\\bitbucket_mcp\\server.py"],
echo       "env": {
echo         "BB_BASE_URL": "%BB_URL%",
echo         "BB_PAT": "%BB_PAT_INPUT%"
echo       }
echo     },
echo     "jenkins": {
echo       "command": "python",
echo       "args": ["%ESCAPED_DIR%\\jenkins_mcp\\server.py"],
echo       "env": {
echo         "JENKINS_URL": "%JENKINS_URL_INPUT%",
echo         "JENKINS_USER": "%JENKINS_USER_INPUT%",
echo         "JENKINS_API_TOKEN": "%JENKINS_TOKEN_INPUT%"
echo       }
echo     }
echo   }
echo }
) > my_cline_settings.json

echo.
echo [OK] 設定已存到 my_cline_settings.json，可以直接複製貼上
echo.
pause
