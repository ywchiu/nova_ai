# Nova MCP Servers

讓 VSCode + Cline 直接操作 Jira、BitBucket、Jenkins 的 MCP Server 套件。

---

## 什麼是 MCP？

MCP（Model Context Protocol）是 Anthropic 制定的開放標準，讓 AI 助理（例如 Cline）可以安全地呼叫外部系統的 API。本套件實作了三個 MCP Server，讓你在 VSCode 裡直接用自然語言操作公司的開發工具。

---

## 系統需求

| 項目 | 版本 |
|------|------|
| Python | 3.10 以上 |
| VSCode | 最新版 |
| Cline 擴充套件 | 最新版 |
| Jira | 9.12.2（Data Center）|
| BitBucket | 8.19.8（Data Center）|
| Jenkins | 最新版 |

---

## 快速安裝

### 步驟一：安裝 Python 套件

```bash
pip3 install -r requirements.txt
```

### 步驟二：取得各系統的 Token

**Jira PAT（Personal Access Token）**
1. 登入 Jira → 右上角頭像 → **Profile**
2. 左側選單 → **Personal Access Tokens** → **Create token**
3. 輸入名稱後複製 token

**BitBucket HTTP Access Token**
1. 登入 BitBucket → 右上角頭像 → **Manage Account**
2. 左側選單 → **HTTP Access Tokens** → **Create token**
3. 權限選 `Project read` + `Repository admin`，複製 token

**Jenkins API Token**
1. 登入 Jenkins → 右上角帳號名稱 → **Configure**
2. 找到 **API Token** → **Add new Token** → **Generate**，複製 token

---

### 步驟三：設定 Cline

1. 開啟 VSCode
2. 按 `Ctrl+Shift+P`（Mac 為 `Cmd+Shift+P`）
3. 輸入 **Cline: Open MCP Settings**，按 Enter
4. 將以下設定貼入（記得替換路徑與 Token）：

```json
{
  "mcpServers": {
    "jira": {
      "command": "python3",
      "args": ["/你的路徑/mcp-servers/jira_mcp/server.py"],
      "env": {
        "JIRA_BASE_URL": "http://你的Jira伺服器",
        "JIRA_PAT": "貼上你的Jira PAT"
      }
    },
    "bitbucket": {
      "command": "python3",
      "args": ["/你的路徑/mcp-servers/bitbucket_mcp/server.py"],
      "env": {
        "BB_BASE_URL": "http://你的BitBucket伺服器",
        "BB_PAT": "貼上你的BitBucket Token"
      }
    },
    "jenkins": {
      "command": "python3",
      "args": ["/你的路徑/mcp-servers/jenkins_mcp/server.py"],
      "env": {
        "JENKINS_URL": "http://你的Jenkins伺服器",
        "JENKINS_USER": "你的帳號",
        "JENKINS_API_TOKEN": "貼上你的Jenkins API Token"
      }
    }
  }
}
```

5. 存檔，Cline 會自動啟動三個 MCP Server

> **Windows 路徑範例：** `C:\\Users\\david\\mcp-servers\\jira_mcp\\server.py`

---

## 可用工具

### Jira

| 工具名稱 | 功能說明 |
|----------|----------|
| `jira_get_issue` | 用 key 取得 issue 詳情，例如 PROJ-123 |
| `jira_search_issues` | 用 JQL 搜尋 issues，支援分頁 |
| `jira_create_issue` | 建立新 issue |
| `jira_update_issue` | 更新 issue 欄位（標題、描述、優先度等）|
| `jira_add_comment` | 在 issue 新增留言 |
| `jira_get_transitions` | 查詢可執行的狀態轉換清單 |
| `jira_transition_issue` | 執行狀態轉換（例如：待辦 → 進行中）|
| `jira_list_projects` | 列出所有可存取的專案 |
| `jira_get_sprint_issues` | 取得目前 sprint 的所有 issues |

### BitBucket

| 工具名稱 | 功能說明 |
|----------|----------|
| `bitbucket_list_repos` | 列出 project 下的所有 repository |
| `bitbucket_list_prs` | 列出 PR（可依 OPEN/MERGED/DECLINED 過濾）|
| `bitbucket_get_pr` | 取得 PR 詳情與最近活動記錄 |
| `bitbucket_create_pr` | 建立新的 Pull Request |
| `bitbucket_add_pr_comment` | 在 PR 新增 review 留言 |
| `bitbucket_list_branches` | 列出分支（可依名稱過濾）|
| `bitbucket_get_file` | 取得指定檔案的原始內容 |
| `bitbucket_list_commits` | 列出最近的 commit 記錄 |

### Jenkins

| 工具名稱 | 功能說明 |
|----------|----------|
| `jenkins_list_jobs` | 列出 jobs（支援 Folder 結構）|
| `jenkins_get_job` | 取得 job 詳情與健康狀態 |
| `jenkins_trigger_build` | 觸發 build（支援帶參數）|
| `jenkins_get_build` | 取得 build 結果與測試報告摘要 |
| `jenkins_get_build_log` | 取得 console log（可指定最後幾字元）|
| `jenkins_list_builds` | 列出最近幾次 build 的結果 |
| `jenkins_get_queue` | 查看目前 build queue |
| `jenkins_cancel_build` | 終止正在執行的 build |
| `jenkins_get_nodes` | 查看所有 agent nodes 狀態 |
| `jenkins_get_job_config` | 取得 job 的 config.xml（Pipeline 設定）|

---

## 使用範例

在 Cline 對話框直接輸入：

```
搜尋 NOVA 專案裡指派給我的、狀態是 In Progress 的所有 issues
```

```
列出 nova-backend 這個 repo 目前 OPEN 的 PR，以及每個 PR 的 reviewer 審查狀態
```

```
幫我觸發 Jenkins 的 nova-backend-deploy job，參數 BRANCH=main、ENV=staging
```

```
取得 nova-backend-deploy 最後一次 build 失敗的 console log
```

```
把 PROJ-456 的狀態改為 Done，並留言「已部署至 production」
```

---

## 檔案結構

```
mcp-servers/
├── jira_mcp/
│   └── server.py          # Jira MCP Server
├── bitbucket_mcp/
│   └── server.py          # BitBucket MCP Server
├── jenkins_mcp/
│   └── server.py          # Jenkins MCP Server
├── requirements.txt       # Python 套件清單
├── cline_mcp_settings.json # Cline 設定範本
├── .env.example           # 環境變數範本
└── README.md              # 本文件
```

---

## 常見問題

**Q: Cline 顯示 MCP Server 無法啟動？**
先在終端機手動測試：
```bash
JIRA_BASE_URL=http://你的伺服器 JIRA_PAT=你的token python3 jira_mcp/server.py
```
如果有錯誤訊息，通常是套件未安裝或環境變數未設定。

**Q: 呼叫工具時出現 401 錯誤？**
Token 驗證失敗。請確認：
- Jira/BitBucket PAT 是否已過期（可在各系統的 Token 管理頁面確認）
- Jenkins API Token 和帳號是否正確

**Q: Jenkins 呼叫 POST 類工具出現 403？**
Jenkins 有 CSRF 保護。本 server 已自動處理 crumb 取得，若仍出現 403，請確認帳號有足夠權限。

**Q: Windows 環境下 python3 找不到？**
改用 `python`（不加 3），或確認 Python 已加入 PATH 環境變數。

---

## 技術說明

- **傳輸方式**：stdio（Cline 直接啟動 Python 子程序，不需開 port）
- **認證方式**：Jira/BitBucket 用 PAT Bearer Token；Jenkins 用 Basic Auth + CSRF crumb
- **API 版本**：Jira REST API v2 `/rest/api/2/`；BitBucket Data Center REST API v1 `/rest/api/1.0/`
- **非同步**：全部工具使用 `async/await` + `httpx` 非同步 HTTP client
