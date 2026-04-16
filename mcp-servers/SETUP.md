# Nova MCP Servers — 安裝說明

## 架構

```
VSCode + Cline
    │
    ├─ stdio ──▶ jira_mcp/server.py       (Jira 9.12.2 Data Center)
    ├─ stdio ──▶ bitbucket_mcp/server.py  (BitBucket 8.19.8 Data Center)
    └─ stdio ──▶ jenkins_mcp/server.py    (Jenkins latest)
```

Cline 用 **stdio** 啟動這 3 個 Python 子程序。不需要開 port，也不用跑任何服務。

---

## 步驟一：安裝 Python 套件

```bash
cd mcp-servers
pip3 install -r requirements.txt
```

---

## 步驟二：確認可以執行

```bash
# 測試語法是否正確
python3 -m py_compile jira_mcp/server.py
python3 -m py_compile bitbucket_mcp/server.py
python3 -m py_compile jenkins_mcp/server.py
```

沒有任何輸出 = 正常。

---

## 步驟三：取得各系統的 Token

### Jira PAT（Personal Access Token）
1. 登入 Jira → 右上角頭像 → **Profile**
2. 左側 → **Personal Access Tokens**
3. **Create token** → 輸入名稱 → 複製 token

### BitBucket PAT
1. 登入 BitBucket → 右上角頭像 → **Manage Account**
2. 左側 → **HTTP Access Tokens**
3. **Create token** → 選 `Project read` + `Repository admin` → 複製

### Jenkins API Token
1. 登入 Jenkins → 右上角帳號 → **Configure**
2. 找到 **API Token** → **Add new Token** → **Generate** → 複製

---

## 步驟四：設定 Cline

1. 開啟 VSCode
2. 按 `Ctrl+Shift+P` → 輸入 **Cline: Open MCP Settings**
3. 把 `cline_mcp_settings.json` 的內容貼進去
4. 把路徑、URL、Token 換成實際的值：

```json
{
  "mcpServers": {
    "jira": {
      "command": "python3",
      "args": ["C:/Users/xxx/mcp-servers/jira_mcp/server.py"],
      "env": {
        "JIRA_BASE_URL": "http://your-jira-server.com",
        "JIRA_PAT": "你的-jira-pat"
      }
    },
    "bitbucket": {
      "command": "python3",
      "args": ["C:/Users/xxx/mcp-servers/bitbucket_mcp/server.py"],
      "env": {
        "BB_BASE_URL": "http://your-bitbucket-server.com",
        "BB_PAT": "你的-bitbucket-pat"
      }
    },
    "jenkins": {
      "command": "python3",
      "args": ["C:/Users/xxx/mcp-servers/jenkins_mcp/server.py"],
      "env": {
        "JENKINS_URL": "http://your-jenkins-server.com",
        "JENKINS_USER": "你的帳號",
        "JENKINS_API_TOKEN": "你的-jenkins-api-token"
      }
    }
  }
}
```

5. 存檔 → Cline 會自動重啟 MCP servers

---

## 步驟五：用 MCP Inspector 測試（選用）

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

## 可用工具列表

### Jira（9 個工具）
| Tool | 功能 |
|------|------|
| `jira_get_issue` | 用 key 取得 issue 詳情（例如 PROJ-123）|
| `jira_search_issues` | JQL 搜尋，支援分頁 |
| `jira_create_issue` | 建立新 issue |
| `jira_update_issue` | 更新 issue 欄位 |
| `jira_add_comment` | 新增留言 |
| `jira_get_transitions` | 查詢可用的狀態轉換 |
| `jira_transition_issue` | 執行狀態轉換（例如：In Progress → Done）|
| `jira_list_projects` | 列出所有專案 |
| `jira_get_sprint_issues` | 取得目前 sprint 的所有 issues |

### BitBucket（8 個工具）
| Tool | 功能 |
|------|------|
| `bitbucket_list_repos` | 列出 project 下的 repositories |
| `bitbucket_list_prs` | 列出 PR（可過濾 OPEN/MERGED/DECLINED）|
| `bitbucket_get_pr` | 取得 PR 詳情和最近活動 |
| `bitbucket_create_pr` | 建立 PR |
| `bitbucket_add_pr_comment` | 在 PR 新增留言 |
| `bitbucket_list_branches` | 列出分支（可依名稱過濾）|
| `bitbucket_get_file` | 取得檔案原始內容 |
| `bitbucket_list_commits` | 列出最近 commits |

### Jenkins（9 個工具）
| Tool | 功能 |
|------|------|
| `jenkins_list_jobs` | 列出 jobs（支援 folder）|
| `jenkins_get_job` | 取得 job 詳情和健康狀態 |
| `jenkins_trigger_build` | 觸發 build（支援帶參數）|
| `jenkins_get_build` | 取得 build 結果和測試報告 |
| `jenkins_get_build_log` | 取得 console log（最後 N 字元）|
| `jenkins_list_builds` | 列出最近幾次 build |
| `jenkins_get_queue` | 查看 build queue |
| `jenkins_cancel_build` | 終止 build |
| `jenkins_get_nodes` | 查看 agent nodes 狀態 |

---

## 在 Cline 裡的使用範例

```
幫我搜尋 NOVA 專案裡指派給我的、狀態是 In Progress 的所有 Jira issues

列出 nova-backend 這個 BitBucket repo 裡目前 OPEN 的 PR

幫我觸發 Jenkins 的 nova-backend-deploy job，參數 BRANCH=main、ENV=staging

取得 nova-backend-deploy 最後一次 build 的 console log，最後 3000 字
```
