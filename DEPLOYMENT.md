# 部署指南 — Windows 環境 + VSCode + Cline

本文件說明如何在客戶的 Windows 電腦上部署 MCP Server，讓所有學員可以使用。

---

## 一、事前準備（你要先確認的事）

### 客戶端需要的資訊

在去之前，跟客戶確認：

| 項目 | 需要什麼 | 誰提供 |
|------|---------|--------|
| **Jira URL** | `http://jira.novatek.com` 或類似 | 客戶 IT |
| **Jira PAT** | 每位學員自己建，或 IT 提供一組共用的 | 客戶 IT |
| **BitBucket URL** | `http://bitbucket.novatek.com` | 客戶 IT |
| **BitBucket PAT** | 同上 | 客戶 IT |
| **Jenkins URL** | `http://jenkins.novatek.com` | 客戶 IT |
| **Jenkins User + API Token** | 同上 | 客戶 IT |
| **Python 版本** | 3.10 以上，確認已安裝 | 客戶 IT |
| **網路** | 電腦能連到 Jira / BB / Jenkins | 客戶 IT |
| **Cline API Key** | 聯詠內部 API 或 Anthropic Key | 客戶 / 你 |

### 你要帶的東西

- [ ] 本 repo 的 zip 或 USB（萬一 git clone 不通）
- [ ] Python 3.10+ 安裝檔（萬一客戶電腦沒裝）
- [ ] 這份 DEPLOYMENT.md（印出來或存手機）

---

## 二、安裝步驟（每台電腦）

### Step 1：取得程式碼

```powershell
# 方式 A：git clone（如果有 git）
git clone https://github.com/ywchiu/nova_ai.git
cd nova_ai\mcp-servers

# 方式 B：解壓縮 zip
# 把 USB 裡的 nova_ai.zip 解壓到 C:\Users\學員\nova_ai
cd C:\Users\學員\nova_ai\mcp-servers
```

### Step 2：安裝 Python 套件

```powershell
# 確認 Python 版本
python --version

# 安裝套件
pip install -r requirements.txt
```

> **注意**：Windows 用 `python`（不是 `python3`）

### Step 3：確認語法正確

```powershell
python -m py_compile jira_mcp\server.py
python -m py_compile bitbucket_mcp\server.py
python -m py_compile jenkins_mcp\server.py
```

沒有輸出 = 正確。

### Step 4：建立 .env

```powershell
copy .env.example .env
notepad .env
```

填入客戶的實際值：

```ini
# Data Center（聯詠內部）
JIRA_BASE_URL=http://jira.novatek.com
JIRA_PAT=學員的PAT

BB_BASE_URL=http://bitbucket.novatek.com
BB_PAT=學員的PAT

JENKINS_URL=http://jenkins.novatek.com
JENKINS_USER=學員帳號
JENKINS_API_TOKEN=學員的token
```

> **Token 含 `=` 號時要加雙引號**：`BB_PAT="ATATT3xF...=1526544D"`

### Step 5：設定 Cline MCP

1. 開啟 VSCode
2. `Ctrl+Shift+P` → 輸入 `Cline: Open MCP Settings`
3. 貼入以下設定（**替換路徑**）：

```json
{
  "mcpServers": {
    "jira": {
      "command": "python",
      "args": ["C:\\Users\\學員\\nova_ai\\mcp-servers\\jira_mcp\\server.py"],
      "env": {
        "JIRA_BASE_URL": "http://jira.novatek.com",
        "JIRA_PAT": "學員的PAT"
      }
    },
    "bitbucket": {
      "command": "python",
      "args": ["C:\\Users\\學員\\nova_ai\\mcp-servers\\bitbucket_mcp\\server.py"],
      "env": {
        "BB_BASE_URL": "http://bitbucket.novatek.com",
        "BB_PAT": "學員的PAT"
      }
    },
    "jenkins": {
      "command": "python",
      "args": ["C:\\Users\\學員\\nova_ai\\mcp-servers\\jenkins_mcp\\server.py"],
      "env": {
        "JENKINS_URL": "http://jenkins.novatek.com",
        "JENKINS_USER": "學員帳號",
        "JENKINS_API_TOKEN": "學員的token"
      }
    }
  }
}
```

4. 存檔 → Cline 自動重啟 MCP servers
5. 左下角應該顯示三個 MCP server 為綠色

> **Windows 路徑注意**：用 `\\` 雙反斜線，或改用 `/` 正斜線都可以

---

## 三、測試流程（確認全部通）

### 快速測試腳本

在 `mcp-servers` 目錄下跑：

```powershell
# 測試 Jira 連線
python -c "import asyncio; from jira_mcp.server import jira_list_projects; print(asyncio.run(jira_list_projects()))"

# 測試 BitBucket 連線
python -c "import asyncio; from bitbucket_mcp.server import bitbucket_list_repos, ListReposInput; print(asyncio.run(bitbucket_list_repos(ListReposInput(project_key='NOVA'))))"

# 測試 Jenkins 連線
python -c "import asyncio; from jenkins_mcp.server import jenkins_list_jobs, ListJobsInput; print(asyncio.run(jenkins_list_jobs(ListJobsInput())))"
```

三個都有回傳 JSON = 全部通。

### 在 Cline 裡測試

開啟 Cline 對話框，依序輸入：

```
列出所有 Jira 專案
```
→ 應回傳專案清單

```
列出 Jenkins 的所有 jobs
```
→ 應回傳 job 清單

```
列出 NOVA 專案的 BitBucket repos
```
→ 應回傳 repo 清單（project key 依客戶實際情況調整）

### 完整測試（用 pytest）

```powershell
# 如果客戶有 pytest
pip install pytest pytest-asyncio

# 跑 Jira 測試
python -m pytest jira_mcp\test_server.py -v -k "查詢"

# 跑 Jenkins 測試（需要 Jenkins 有測試 jobs）
python -m pytest jenkins_mcp\test_server.py -v -k "查詢"
```

---

## 四、讓所有學員都能用

### 方案 A：每人獨立 Token（推薦）

每位學員用自己的帳號建 PAT/Token：

| 系統 | 建立位置 |
|------|---------|
| Jira | Profile → Personal Access Tokens → Create token |
| BitBucket | Manage Account → HTTP Access Tokens → Create token |
| Jenkins | 帳號 → Configure → API Token → Add new Token |

**優點**：權限獨立、可追蹤誰做了什麼
**缺點**：每人要花 5 分鐘建 token

### 方案 B：共用 Token（快速但不推薦用於正式環境）

IT 建一組共用的唯讀帳號，所有學員共用：

```ini
# 所有學員共用這組
JIRA_PAT=IT提供的共用token
BB_PAT=IT提供的共用token
JENKINS_USER=training
JENKINS_API_TOKEN=IT提供的共用token
```

**優點**：設定快，5 分鐘搞定全班
**缺點**：無法追蹤個人操作、共用帳號安全風險較高

### 方案 C：課堂快速部署腳本

建立一個批次檔，讓學員一鍵設定：

```bat
@echo off
echo === Nova MCP Setup ===

set /p STUDENT_NAME="請輸入你的名字: "
set /p JIRA_PAT="請貼上你的 Jira PAT: "
set /p BB_PAT="請貼上你的 BitBucket PAT: "
set /p JENKINS_USER="請輸入 Jenkins 帳號: "
set /p JENKINS_TOKEN="請貼上 Jenkins API Token: "

echo JIRA_BASE_URL=http://jira.novatek.com > .env
echo JIRA_PAT=%JIRA_PAT% >> .env
echo BB_BASE_URL=http://bitbucket.novatek.com >> .env
echo BB_PAT=%BB_PAT% >> .env
echo JENKINS_URL=http://jenkins.novatek.com >> .env
echo JENKINS_USER=%JENKINS_USER% >> .env
echo JENKINS_API_TOKEN=%JENKINS_TOKEN% >> .env

echo.
echo === .env 建立完成 ===
echo 接下來請設定 Cline MCP Settings
pause
```

---

## 五、常見問題排除

### Python 找不到

```
'python' 不是內部或外部命令
```

→ Python 沒裝或沒加入 PATH。
→ 解法：`控制台 → 系統 → 環境變數 → Path → 加入 Python 安裝路徑`
→ 或用完整路徑：`C:\Python310\python.exe`

### pip install 失敗（公司防火牆）

```
Could not fetch URL https://pypi.org/...
```

→ 公司可能有 proxy 或內部 PyPI mirror
→ 問 IT 拿 proxy 設定：
```powershell
pip install -r requirements.txt --proxy http://proxy.novatek.com:8080
```
→ 或事先在 USB 裡準備好 wheel 檔：
```powershell
# 你在有網路的電腦先下載
pip download -r requirements.txt -d packages/

# 學員電腦離線安裝
pip install --no-index --find-links=packages/ -r requirements.txt
```

### Cline MCP Server 紅燈

→ 先在終端機手動測試：
```powershell
set JIRA_BASE_URL=http://jira.novatek.com
set JIRA_PAT=你的token
python jira_mcp\server.py
```
→ 看錯誤訊息，通常是 token 錯或 URL 不通

### 連不到 Jira / BitBucket / Jenkins

→ 先用瀏覽器確認 URL 能開
→ 確認 VPN 有沒有開（如果需要）
→ 確認防火牆沒有擋 Python 的網路存取

### Token 含 = 號導致認證失敗

→ 在 .env 裡用雙引號包起來：
```ini
BB_PAT="ATATT3xF...=1526544D"
```

---

## 六、課堂時間安排建議

| 時間 | 動作 | 備註 |
|------|------|------|
| 課前 30 分 | 確認講師電腦全部通 | 跑快速測試腳本 |
| 課前 15 分 | 學員裝 Python + pip install | 可以先寫在白板 |
| M5 開始時 | 學員設定 .env + Cline | 用方案 C 批次檔最快 |
| M6 開始時 | 在 Cline 裡測試三個連線 | 確認全班都綠燈 |

---

## 七、離線備案

如果客戶網路完全不通（最壞情況）：

1. **用你的筆電 demo** — 連你自己的 Jira Cloud + BitBucket Cloud
2. **錄一段操作影片** — 事先錄好完整 demo 流程
3. **用 MCP Inspector** — 本機可以跑，不需要連外部系統：
   ```powershell
   npx @modelcontextprotocol/inspector python jira_mcp\server.py
   ```
