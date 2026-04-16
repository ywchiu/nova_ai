# Nova MCP Servers — 安裝指引

---

## 架構

```
VSCode + Cline（或 Claude Code）
    │
    ├─ stdio ──▶ jira_mcp/server.py       → Jira 9.12.2 (Data Center)
    ├─ stdio ──▶ bitbucket_mcp/server.py  → BitBucket 8.19.8 (Data Center)
    └─ stdio ──▶ jenkins_mcp/server.py    → Jenkins (LTS)
```

Cline 用 **stdio** 啟動 Python 子程序，不需要開 port，也不用另外跑服務。

---

## 步驟一：安裝 Python 套件

```bash
cd mcp-servers
pip3 install -r requirements.txt
```

需要的套件：
- `mcp[cli]` — MCP 協定核心
- `httpx` — 非同步 HTTP client
- `pydantic` — 輸入驗證
- `python-dotenv` — 環境變數讀取

---

## 步驟二：確認語法正確

```bash
python3 -m py_compile jira_mcp/server.py
python3 -m py_compile bitbucket_mcp/server.py
python3 -m py_compile jenkins_mcp/server.py
```

沒有任何輸出 = 正常。

---

## 步驟三：取得各系統的 Token

### Jira PAT（Personal Access Token）

1. 登入 Jira → 右上角頭像 → **Profile**
2. 左側選單 → **Personal Access Tokens**
3. **Create token** → 輸入名稱 → 複製 token

### BitBucket HTTP Access Token

1. 登入 BitBucket → 右上角頭像 → **Manage Account**
2. 左側選單 → **HTTP Access Tokens**
3. **Create token** → 權限選 `Project read` + `Repository admin` → 複製

### Jenkins API Token

1. 登入 Jenkins → 右上角帳號名稱 → **Configure**
2. 找到 **API Token** → **Add new Token** → **Generate** → 複製

---

## 步驟四：設定 Cline（VSCode）

1. 開啟 VSCode
2. 按 `Ctrl+Shift+P`（Mac 為 `Cmd+Shift+P`）
3. 輸入 **Cline: Open MCP Settings**，按 Enter
4. 貼入以下設定（替換路徑與 Token）：

```json
{
  "mcpServers": {
    "jira": {
      "command": "python3",
      "args": ["/你的路徑/mcp-servers/jira_mcp/server.py"],
      "env": {
        "JIRA_BASE_URL": "http://你的Jira伺服器",
        "JIRA_PAT": "貼上你的 Jira PAT"
      }
    },
    "bitbucket": {
      "command": "python3",
      "args": ["/你的路徑/mcp-servers/bitbucket_mcp/server.py"],
      "env": {
        "BB_BASE_URL": "http://你的BitBucket伺服器",
        "BB_PAT": "貼上你的 BitBucket Token"
      }
    },
    "jenkins": {
      "command": "python3",
      "args": ["/你的路徑/mcp-servers/jenkins_mcp/server.py"],
      "env": {
        "JENKINS_URL": "http://你的Jenkins伺服器",
        "JENKINS_USER": "你的帳號",
        "JENKINS_API_TOKEN": "貼上你的 Jenkins API Token"
      }
    }
  }
}
```

5. 存檔 → Cline 會自動啟動三個 MCP Server

> **Windows 路徑範例：** `C:\\Users\\david\\mcp-servers\\jira_mcp\\server.py`

---

## 步驟五：用 MCP Inspector 測試（選用）

MCP Inspector 可以在瀏覽器中直接測試各個工具：

```bash
# 測試 Jira
JIRA_BASE_URL=http://jira.company.com JIRA_PAT=xxx \
  npx @modelcontextprotocol/inspector python3 jira_mcp/server.py

# 測試 BitBucket
BB_BASE_URL=http://bitbucket.company.com BB_PAT=xxx \
  npx @modelcontextprotocol/inspector python3 bitbucket_mcp/server.py

# 測試 Jenkins
JENKINS_URL=http://jenkins.company.com JENKINS_USER=xxx JENKINS_API_TOKEN=xxx \
  npx @modelcontextprotocol/inspector python3 jenkins_mcp/server.py
```

---

## 本機測試環境（Docker）

如果沒有現成的 Jira / BitBucket / Jenkins，可以用 Docker 在本機建立測試環境。

### 前置需求

- Docker Desktop（已啟動）
- 至少 6GB 可用記憶體（跑全部服務時）

### 啟動服務

```bash
cd mcp-servers/docker

# 方式一：只啟動 Jenkins（約 512MB，適合 CI/CD 演練）
docker compose up -d jenkins

# 方式二：啟動全部（Jira + BitBucket + Jenkins + PostgreSQL）
docker compose up -d
```

### 服務網址

| 服務 | 網址 | 預設帳號 |
|------|------|---------|
| Jenkins | http://localhost:9090 | 初始密碼見下方 |
| Jira | http://localhost:8080 | 需完成設定精靈 |
| BitBucket | http://localhost:7990 | 需完成設定精靈 |
| PostgreSQL | localhost:5432 | postgres / nova1234 |

### Jenkins 初始設定

```bash
# 1. 取得初始管理員密碼
docker exec nova-jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# 2. 開啟 http://localhost:9090，貼上密碼
# 3. 選擇「Install suggested plugins」
# 4. 建立管理員帳號（建議 admin / admin1234）
# 5. 完成設定
```

### 取得 Jenkins API Token

```bash
# 登入 Jenkins 後：
# 右上角帳號名稱 → Configure → API Token → Add new Token → Generate → 複製
```

### 建立測試用 Jobs

```bash
cd mcp-servers

export JENKINS_URL=http://localhost:9090
export JENKINS_USER=admin
export JENKINS_API_TOKEN=你的token

# 自動建立 10 個測試 Jobs（包含 Pipeline）
python jenkins_mcp/setup_test_jobs.py
```

建立的 Jobs：

| Job 名稱 | 類型 | 說明 |
|----------|------|------|
| `mcp-test-job` | Freestyle | 簡單的 echo |
| `mcp-param-job` | Freestyle | 帶 BRANCH / ENV 參數 |
| `mcp-fail-job` | Freestyle | 永遠失敗（exit 1） |
| `mcp-slow-job` | Freestyle | sleep 30 秒（測試取消功能） |
| `TestFolder/nested-job` | Freestyle | 放在 Folder 裡（測試路徑處理） |
| `pipeline-cicd` | Pipeline | 多階段 CI/CD（Checkout → Build → Test → Deploy） |
| `pipeline-fail-stage` | Pipeline | Test 階段失敗的 Pipeline |
| `pipeline-pr-review` | Pipeline | PR → Review → Build → Report |
| `chip-validator-ci` | Pipeline | 真實 pytest CI（21 個測試） |
| `chip-validator-ci-fail` | Pipeline | 注入 bug 的 CI（展示失敗診斷） |

### 跑整合測試

```bash
# 全部跑（38 個測試）
pytest jenkins_mcp/ -v

# 只跑基礎測試（19 個）
pytest jenkins_mcp/test_server.py -v

# 只跑 Pipeline 測試（11 個）
pytest jenkins_mcp/test_pipeline.py -v

# 只跑 CI/CD Demo（8 個）
pytest jenkins_mcp/test_demo_cicd.py -v -s
```

### 停止 / 清除

```bash
cd mcp-servers/docker

# 停止服務（保留資料）
docker compose down

# 完全清除（含所有資料）
docker compose down -v
```

---

## 可用工具列表

### Jira（9 個工具）

| 工具名稱 | 功能說明 |
|----------|---------|
| `jira_get_issue` | 用 key 取得 issue 詳情（例如 PROJ-123） |
| `jira_search_issues` | 用 JQL 搜尋 issues，支援分頁 |
| `jira_create_issue` | 建立新 issue |
| `jira_update_issue` | 更新 issue 欄位（標題、描述、優先度等） |
| `jira_add_comment` | 在 issue 新增留言 |
| `jira_get_transitions` | 查詢可執行的狀態轉換清單 |
| `jira_transition_issue` | 執行狀態轉換（例如：待辦 → 進行中） |
| `jira_list_projects` | 列出所有可存取的專案 |
| `jira_get_sprint_issues` | 取得目前 sprint 的所有 issues |

### BitBucket（8 個工具）

| 工具名稱 | 功能說明 |
|----------|---------|
| `bitbucket_list_repos` | 列出 project 下的所有 repository |
| `bitbucket_list_prs` | 列出 PR（可依 OPEN / MERGED / DECLINED 過濾） |
| `bitbucket_get_pr` | 取得 PR 詳情與最近活動記錄 |
| `bitbucket_create_pr` | 建立新的 Pull Request |
| `bitbucket_add_pr_comment` | 在 PR 新增 review 留言 |
| `bitbucket_list_branches` | 列出分支（可依名稱過濾） |
| `bitbucket_get_file` | 取得指定檔案的原始內容 |
| `bitbucket_list_commits` | 列出最近的 commit 記錄 |

### Jenkins（10 個工具）

| 工具名稱 | 功能說明 |
|----------|---------|
| `jenkins_list_jobs` | 列出 jobs（支援 Folder 結構） |
| `jenkins_get_job` | 取得 job 詳情與健康狀態 |
| `jenkins_trigger_build` | 觸發 build（支援帶參數） |
| `jenkins_get_build` | 取得 build 結果與測試報告摘要 |
| `jenkins_get_build_log` | 取得 console log（可指定最後幾字元） |
| `jenkins_list_builds` | 列出最近幾次 build 的結果 |
| `jenkins_get_queue` | 查看目前 build queue |
| `jenkins_cancel_build` | 終止正在執行的 build |
| `jenkins_get_nodes` | 查看所有 agent nodes 狀態 |
| `jenkins_get_job_config` | 取得 job 的 config.xml（Pipeline 設定） |

---

## 在 Cline 裡的使用範例

```
幫我搜尋 NOVA 專案裡指派給我的、狀態是 In Progress 的所有 Jira issues

列出 nova-backend 這個 BitBucket repo 裡目前 OPEN 的 PR

幫我觸發 Jenkins 的 chip-validator-ci job

CI 掛了，幫我看一下怎麼回事

讀取 pipeline-cicd 的 Pipeline 設定，告訴我有哪些 stage
```

---

## 常見問題

**Q: Cline 顯示 MCP Server 無法啟動？**

先在終端機手動測試：
```bash
JENKINS_URL=http://localhost:9090 JENKINS_USER=admin JENKINS_API_TOKEN=你的token \
  python3 jenkins_mcp/server.py
```
如果有錯誤訊息，通常是套件未安裝或環境變數未設定。

**Q: 呼叫工具時出現 401 錯誤？**

Token 驗證失敗。請確認：
- Jira / BitBucket PAT 是否已過期
- Jenkins API Token 和帳號是否正確

**Q: Jenkins 呼叫 POST 類工具出現 403？**

Jenkins 有 CSRF 保護。本 server 已自動處理 crumb 取得。若仍出現 403，請確認帳號有足夠權限。

**Q: Windows 環境下 python3 找不到？**

改用 `python`（不加 3），或確認 Python 已加入 PATH 環境變數。

**Q: Pipeline job 第一次帶參數觸發回傳 400？**

Jenkins Pipeline 的 `parameters {}` 區塊需要第一次 build 後才會生效。先不帶參數觸發一次，之後就可以帶參數了。
