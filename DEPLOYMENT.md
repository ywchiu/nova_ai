# 部署指南 — Nova MCP Servers 完整安裝與設定

本文件是 Nova MCP Servers 的完整部署指南，涵蓋從事前準備到學員分發的所有步驟。

---

## 目錄

- [一、事前準備清單](#一事前準備清單)
- [二、完整安裝流程](#二完整安裝流程)
- [三、設定認證資訊](#三設定認證資訊)
- [四、測試流程](#四測試流程)
- [五、學員分發方式](#五學員分發方式)
- [六、離線安裝方式](#六離線安裝方式)
- [七、課堂時間安排建議](#七課堂時間安排建議)
- [八、常見問題排除](#八常見問題排除)
- [九、相關文件目錄](#九相關文件目錄)

---

## 一、事前準備清單

### 需要跟客戶 MIS/IT 確認的事項

| 項目 | 需要什麼 | 誰提供 | 備註 |
|------|---------|--------|------|
| **Jira URL** | `http://jira.company.com` 或 `https://xxx.atlassian.net` | 客戶 IT | 確認是 Data Center 還是 Cloud |
| **Jira 認證** | PAT（DC）或 Email + API Token（Cloud） | 客戶 IT / 學員 | 見下方說明 |
| **BitBucket URL** | `http://bitbucket.company.com` 或 `https://api.bitbucket.org/2.0` | 客戶 IT | 同上 |
| **BitBucket 認證** | PAT（DC）或 Username + API Token（Cloud） | 客戶 IT / 學員 | 見下方說明 |
| **Jenkins URL** | `http://jenkins.company.com` | 客戶 IT | 只有 Basic Auth |
| **Jenkins 認證** | Username + API Token | 客戶 IT / 學員 | |
| **Python 版本** | 3.10 以上 | 客戶 IT | 確認已安裝並加入 PATH |
| **網路** | 電腦能連到 Jira / BitBucket / Jenkins | 客戶 IT | VPN、防火牆 |
| **Cline API Key** | Anthropic Key 或內部 API | 客戶 / 講師 | |

### 認證方式對照

| 系統 | Data Center（公司自建） | Cloud（SaaS） |
|------|----------------------|--------------|
| **Jira** | `JIRA_PAT`（Bearer Token） | `JIRA_EMAIL` + `JIRA_API_TOKEN`（Basic Auth） |
| **BitBucket** | `BB_PAT`（Bearer Token） | `BB_USER` + `BB_API_TOKEN`（Basic Auth） |
| **Jenkins** | `JENKINS_USER` + `JENKINS_API_TOKEN`（Basic Auth） | 同左 |

### 你要帶的東西

- [ ] 本 repo 的 zip 或 USB 隨身碟
- [ ] Python 3.11 安裝檔（`usb_package/python-3.11.9-amd64.exe`）
- [ ] Git 安裝檔（`usb_package/Git-Windows-amd64.exe`）
- [ ] 離線 pip 套件（`usb_package/packages-win/` 或 `mcp-servers/packages-win/`）
- [ ] 這份 DEPLOYMENT.md

---

## 二、完整安裝流程

### 方式 A：使用 PowerShell 一鍵安裝（推薦）

#### Step 1：取得程式碼

```powershell
# git clone（如果有 git）
git clone https://github.com/ywchiu/nova_ai.git
cd nova_ai\mcp-servers

# 或解壓縮 USB 裡的 zip
# 解壓 usb_package\nova_ai.zip 到 C:\Users\學員\nova_ai
cd C:\Users\學員\nova_ai\mcp-servers
```

#### Step 2：一鍵安裝

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

這個腳本會自動：
1. 檢查 Python 版本（3.10+）
2. 安裝 pip 套件（先試線上，失敗自動嘗試離線 `packages-win/`）
3. 驗證三個 server.py 語法正確

#### Step 3：設定認證

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup-env.ps1
```

互動式精靈會：
1. 詢問 Cloud 還是 Data Center
2. 依選擇提示輸入對應的認證資訊
3. 自動產生 `.env` 檔
4. 自動產生 `my_cline_settings.json`（可直接貼入 Cline）

#### Step 4：測試連線

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test-connection.ps1
```

顯示三個 MCP Server 的連線結果表格。

### 方式 B：手動安裝

如果 PowerShell 腳本有問題，可以手動執行：

```powershell
# 確認 Python
python --version

# 安裝套件
pip install -r requirements.txt

# 語法檢查
python -m py_compile jira_mcp\server.py
python -m py_compile bitbucket_mcp\server.py
python -m py_compile jenkins_mcp\server.py

# 建立 .env
copy .env.example .env
notepad .env    # 手動填入認證資訊
```

### 方式 C：使用 setup_student.bat（舊版批次檔）

```powershell
setup_student.bat
```

> **注意**：`setup_student.bat` 只支援 Data Center 模式，Cloud 請用 `scripts\setup-env.ps1`。

---

## 三、設定認證資訊

### Data Center 模式

`.env` 檔內容：

```ini
# Jira（Data Center）
JIRA_BASE_URL=http://jira.company.com
JIRA_PAT=你的Jira_PAT

# BitBucket（Data Center）
BB_BASE_URL=http://bitbucket.company.com
BB_PAT=你的BitBucket_PAT

# Jenkins
JENKINS_URL=http://jenkins.company.com
JENKINS_USER=你的帳號
JENKINS_API_TOKEN=你的Jenkins_Token
```

### Cloud 模式

```ini
# Jira（Cloud）
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=你的Jira_API_Token

# BitBucket（Cloud）
BB_BASE_URL=https://api.bitbucket.org/2.0
BB_USER=your-username
BB_API_TOKEN=你的BitBucket_App_Password

# Jenkins
JENKINS_URL=http://jenkins.company.com
JENKINS_USER=你的帳號
JENKINS_API_TOKEN=你的Jenkins_Token
```

> **重要**：Token 含 `=` 號時要加雙引號，例如：`BB_PAT="ATATT3xF...=1526544D"`

### 設定 Cline MCP

1. 開啟 VSCode
2. `Ctrl+Shift+P` → 輸入 `Cline: Open MCP Settings`
3. 貼入 `my_cline_settings.json` 的內容（由 `setup-env.ps1` 自動產生）
4. 存檔 → Cline 自動重啟 MCP Servers
5. 左下角應該顯示三個 MCP Server 為綠色

> **Windows 路徑注意**：JSON 裡用 `\\` 雙反斜線或 `/` 正斜線。Windows 用 `python`（不是 `python3`）。

---

## 四、測試流程

### 自動化測試（推薦）

```powershell
# 連線測試（快速確認三個 Server 都通）
powershell -ExecutionPolicy Bypass -File scripts\test-connection.ps1

# 完整測試（跑所有 pytest 測試）
powershell -ExecutionPolicy Bypass -File scripts\run-all-tests.ps1
```

### 手動快速測試

```powershell
# 測試 Jira
python -c "import asyncio; from jira_mcp.server import jira_list_projects; print(asyncio.run(jira_list_projects()))"

# 測試 BitBucket
python -c "import asyncio; from bitbucket_mcp.server import bitbucket_list_repos, ListReposInput; print(asyncio.run(bitbucket_list_repos(ListReposInput())))"

# 測試 Jenkins
python -c "import asyncio; from jenkins_mcp.server import jenkins_list_jobs, ListJobsInput; print(asyncio.run(jenkins_list_jobs(ListJobsInput())))"
```

三個都有回傳 JSON = 全部通。

### 在 Cline 裡測試

開啟 Cline 對話框，依序測試：

```
列出所有 Jira 專案
```

```
列出 Jenkins 的所有 jobs
```

```
列出 NOVA 專案的 BitBucket repos
```

---

## 五、學員分發方式

### 方案 A：每人獨立 Token（推薦）

每位學員用自己的帳號建 PAT/Token：

| 系統 | 建立位置 |
|------|---------|
| Jira DC | Profile → Personal Access Tokens → Create token |
| Jira Cloud | https://id.atlassian.com/manage-profile/security/api-tokens |
| BitBucket DC | Manage Account → HTTP Access Tokens → Create token |
| BitBucket Cloud | https://bitbucket.org/account/settings/app-passwords/ |
| Jenkins | 帳號 → Configure → API Token → Add new Token |

**優點**：權限獨立、可追蹤誰做了什麼
**缺點**：每人要花 5 分鐘建 token

### 方案 B：共用 Token（快速但不推薦用於正式環境）

IT 建一組共用的唯讀帳號，所有學員共用：

```ini
JIRA_PAT=IT提供的共用token
BB_PAT=IT提供的共用token
JENKINS_USER=training
JENKINS_API_TOKEN=IT提供的共用token
```

**優點**：設定快，5 分鐘搞定全班
**缺點**：無法追蹤個人操作、安全風險

### 方案 C：課堂快速部署

1. 安裝完畢後，每位學員執行：
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\setup-env.ps1
   ```
2. 依指示輸入自己的 Token
3. 把產生的 `my_cline_settings.json` 貼入 Cline

---

## 六、離線安裝方式

適用於客戶網路不通或有嚴格防火牆的環境。

### USB 離線安裝包內容

```
usb_package/
├── python-3.11.9-amd64.exe    # Python 安裝檔
├── Git-Windows-amd64.exe      # Git 安裝檔
├── packages-win/              # pip 離線套件（36 個 .whl）
└── nova_ai.zip                # 完整專案壓縮檔
```

### 離線安裝步驟

1. **安裝 Python**（如果沒有）：
   ```
   執行 usb_package\python-3.11.9-amd64.exe
   勾選「Add Python to PATH」→ Install
   ```

2. **安裝 Git**（如果沒有）：
   ```
   執行 usb_package\Git-Windows-amd64.exe
   全部預設 → Install
   ```

3. **解壓專案**：
   ```
   解壓 usb_package\nova_ai.zip 到 C:\Users\學員\nova_ai
   ```

4. **安裝 pip 套件（離線）**：
   ```powershell
   cd C:\Users\學員\nova_ai\mcp-servers
   pip install --no-index --find-links=..\usb_package\packages-win -r requirements.txt
   ```
   或直接執行 `scripts\install.ps1`，它會自動偵測離線套件目錄。

5. **設定認證**：
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\setup-env.ps1
   ```

### 準備離線套件（講師事前準備）

在有網路的電腦上執行：

```powershell
# 下載 Windows amd64 的 wheel 檔
pip download -r requirements.txt -d packages-win --platform win_amd64 --python-version 3.11 --only-binary=:all:
```

---

## 七、課堂時間安排建議

| 時間 | 動作 | 備註 |
|------|------|------|
| 課前 30 分 | 確認講師電腦全部通 | 跑 `scripts\test-connection.ps1` |
| 課前 15 分 | 學員裝 Python + `scripts\install.ps1` | 可以先寫在白板 |
| M5 開始時 | 學員執行 `scripts\setup-env.ps1` | 互動式設定，2 分鐘搞定 |
| M6 開始時 | 在 Cline 裡測試三個連線 | 確認全班都綠燈 |
| 需要時 | 跑完整測試 `scripts\run-all-tests.ps1` | 83 個測試 |

---

## 八、常見問題排除

### Python 找不到

```
'python' 不是內部或外部命令
```

→ Python 沒裝或沒加入 PATH。
→ 解法：`控制台 → 系統 → 環境變數 → Path → 加入 Python 安裝路徑`
→ 或用完整路徑：`C:\Python311\python.exe`

### PowerShell 執行政策限制

```
無法載入檔案，因為在此系統上停用了指令碼執行
```

→ 用這個指令執行：
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

### pip install 失敗（公司防火牆）

```
Could not fetch URL https://pypi.org/...
```

→ 問 IT 拿 proxy 設定：
```powershell
pip install -r requirements.txt --proxy http://proxy.company.com:8080
```
→ 或用離線安裝（見[六、離線安裝方式](#六離線安裝方式)）

### Cline MCP Server 紅燈

→ 先在終端機手動測試：
```powershell
$env:JIRA_BASE_URL = "http://jira.company.com"
$env:JIRA_PAT = "你的token"
python jira_mcp\server.py
```
→ 看錯誤訊息，通常是 token 錯或 URL 不通

### 連不到 Jira / BitBucket / Jenkins

→ 先用瀏覽器確認 URL 能開
→ 確認 VPN 有沒有開（如果需要）
→ 確認防火牆沒有擋 Python 的網路存取

### Token 含 = 號導致認證失敗

→ 在 `.env` 裡用雙引號包起來：
```ini
BB_PAT="ATATT3xF...=1526544D"
```

### 離線備案（網路完全不通）

1. **用講師筆電 demo** — 連自己的 Jira Cloud + BitBucket Cloud
2. **錄一段操作影片** — 事先錄好完整 demo 流程
3. **用 MCP Inspector** — 本機可以跑，不需要連外部系統：
   ```powershell
   npx @modelcontextprotocol/inspector python jira_mcp\server.py
   ```

---

## 九、相關文件目錄

| 文件 | 路徑 | 說明 |
|------|------|------|
| 安裝腳本 | [`mcp-servers/scripts/install.ps1`](mcp-servers/scripts/install.ps1) | 一鍵安裝 Python 套件 + 語法驗證 |
| 設定腳本 | [`mcp-servers/scripts/setup-env.ps1`](mcp-servers/scripts/setup-env.ps1) | 互動式產生 .env + Cline 設定 |
| 連線測試 | [`mcp-servers/scripts/test-connection.ps1`](mcp-servers/scripts/test-connection.ps1) | 測試三個 MCP Server 連線 |
| 全部測試 | [`mcp-servers/scripts/run-all-tests.ps1`](mcp-servers/scripts/run-all-tests.ps1) | 跑全部 pytest 測試 |
| 學員批次檔 | [`mcp-servers/setup_student.bat`](mcp-servers/setup_student.bat) | 舊版 .bat 設定（僅 DC） |
| 環境變數範本 | [`mcp-servers/.env.example`](mcp-servers/.env.example) | .env 範本 |
| MCP 設定範本 | [`mcp-servers/cline_mcp_settings.json`](mcp-servers/cline_mcp_settings.json) | Cline MCP 設定範本 |
| 套件清單 | [`mcp-servers/requirements.txt`](mcp-servers/requirements.txt) | Python 套件清單 |
| MCP Server 說明 | [`mcp-servers/README.md`](mcp-servers/README.md) | MCP Server 技術文件 |
| 安裝指引 | [`mcp-servers/SETUP.md`](mcp-servers/SETUP.md) | MCP Server 安裝指引 |
| Skill 範例 | [`mcp-servers/skills/`](mcp-servers/skills/) | 三個 Skill 範例 |
| USB 離線包 | [`usb_package/`](usb_package/) | Python/Git 安裝檔 + 離線套件 |
