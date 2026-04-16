# Nova AI — AI 輔助開發實戰專案

本專案為「AI 輔助開發」課程的完整教材，包含 MCP Server 套件與 CI/CD 實機演練環境。

---

## 專案結構

```
nova_ai/
├── mcp-servers/                 # MCP Server 套件（Jira / BitBucket / Jenkins）
│   ├── jira_mcp/server.py       #   Jira MCP Server（9 個工具）
│   ├── bitbucket_mcp/server.py  #   BitBucket MCP Server（8 個工具）
│   ├── jenkins_mcp/server.py    #   Jenkins MCP Server（10 個工具）
│   ├── jenkins_mcp/setup_test_jobs.py   # 自動建立 Jenkins 測試 Jobs
│   ├── jenkins_mcp/test_server.py       # 基礎整合測試（19 個）
│   ├── jenkins_mcp/test_pipeline.py     # Pipeline 整合測試（11 個）
│   ├── jenkins_mcp/test_demo_cicd.py    # CI/CD Demo 端對端測試（8 個）
│   ├── docker/                  #   本機測試用 Docker Compose
│   ├── requirements.txt
│   ├── SETUP.md                 #   安裝指引
│   └── README.md                #   MCP Server 說明文件
├── demo_project/                # CI/CD 實機演練專案
│   └── chip_validator/          #   晶片暫存器設定驗證器
│       ├── models.py            #     Register / BitField / ChipConfig 資料模型
│       ├── validator.py         #     6 條驗證規則
│       └── tests/
│           └── test_validator.py #    21 個 pytest 測試
└── courses_desc/                # 課程大綱
```

---

## 快速開始

### 1. 安裝 Python 套件

```bash
cd mcp-servers
pip3 install -r requirements.txt
```

### 2. 啟動本機測試環境（Docker）

```bash
cd mcp-servers/docker

# 只啟動 Jenkins（最小記憶體需求）
docker compose up -d jenkins

# 或啟動全部（Jira + BitBucket + Jenkins + PostgreSQL，需 6GB+ RAM）
docker compose up -d
```

| 服務 | 網址 | 說明 |
|------|------|------|
| Jenkins | http://localhost:9090 | 初始密碼見 `docker exec nova-jenkins cat /var/jenkins_home/secrets/initialAdminPassword` |
| Jira | http://localhost:8080 | 需完成初始設定精靈 |
| BitBucket | http://localhost:7990 | 需完成初始設定精靈 |

### 3. 設定 MCP Server

詳細步驟請參考 [mcp-servers/SETUP.md](mcp-servers/SETUP.md)。

### 4. 跑 Jenkins 整合測試

```bash
cd mcp-servers

# 設定環境變數
export JENKINS_URL=http://localhost:9090
export JENKINS_USER=admin
export JENKINS_API_TOKEN=你的token

# 建立測試用 Jenkins Jobs（只需跑一次）
python jenkins_mcp/setup_test_jobs.py

# 跑全部測試（38 個）
pytest jenkins_mcp/ -v
```

---

## MCP Server 總覽

### 什麼是 MCP？

MCP（Model Context Protocol）是 Anthropic 制定的開放標準，讓 AI 助理可以安全地呼叫外部系統的 API。本套件實作了三個 MCP Server，對應公司常用的開發工具：

| MCP Server | 對應系統 | 工具數量 | 用途 |
|------------|---------|---------|------|
| `jira_mcp` | Jira 9.12.2 (Data Center) | 9 個 | Issue 管理、Sprint 查詢、狀態轉換 |
| `bitbucket_mcp` | BitBucket 8.19.8 (Data Center) | 8 個 | Repo 管理、PR 操作、程式碼讀取 |
| `jenkins_mcp` | Jenkins (LTS) | 10 個 | Job 管理、Build 觸發/監控、Pipeline 設定讀取 |

### 在 Cline / Claude Code 中使用

```
幫我搜尋 NOVA 專案裡指派給我的、狀態是 In Progress 的所有 Jira issues

列出 nova-backend 的 OPEN PR，以及每個 PR 的 reviewer 審查狀態

幫我觸發 Jenkins 的 chip-validator-ci job

CI 掛了，幫我看一下怎麼回事
```

---

## CI/CD 實機演練

### 專案：chip_validator（晶片暫存器設定驗證器）

模擬 IC 設計公司常見的 register config 驗證場景：

| 驗證規則 | 說明 |
|---------|------|
| 位址範圍 | 暫存器位址必須在 0x0000 ~ 0xFFFF |
| Bit field 重疊 | 同一暫存器內的 bit field 不可重疊 |
| Bit field 寬度 | msb/lsb 不可超出暫存器寬度 |
| 必要暫存器 | CTRL_REG、STATUS_REG 必須存在 |
| Clock 頻率 | 必須在 10 ~ 800 MHz |
| 核心電壓 | 必須在 750 ~ 1100 mV |

### Jenkins Pipeline Jobs

| Job 名稱 | 說明 |
|----------|------|
| `chip-validator-ci` | 完整 CI：Setup → Lint → Test(pytest 21個) → Report |
| `chip-validator-ci-fail` | 注入 bug（改壞 clock 上限）→ 測試失敗 → 自動還原 |

### Demo 流程

**場景 A — Agent 觸發 CI 成功：**
```
使用者：「幫我跑一次 chip-validator 的 CI」
Agent ：觸發 build → 等待 → 回報「21 個測試全部通過」
```

**場景 B — Agent 診斷 CI 失敗：**
```
使用者：「CI 掛了，幫我看一下怎麼回事」
Agent ：查 job 狀態（紅燈）
      → 讀失敗 log → 找到 3 個 FAILED 測試
      → 定位根因：CLOCK_MAX_MHZ 從 800 被改成 100
      → 建議修復方式
```

---

## 課程模組對照

| 課程模組 | 對應資源 |
|---------|---------|
| M2 — MCP 系統串接 | `mcp-servers/` 三個 MCP Server + SETUP.md |
| M4 — CI/CD Pipeline 整合 | `demo_project/chip_validator/` + Pipeline Jobs |
| M6 — MCP 設定與測試 | `test_server.py` + `test_pipeline.py` |
| W1 — Issue 驅動開發 | Jira MCP + BitBucket MCP 搭配使用 |

---

## 技術規格

- **Python**: 3.10+
- **MCP 傳輸**: stdio（不需開 port）
- **HTTP Client**: httpx（非同步）
- **認證方式**:
  - Jira / BitBucket: PAT Bearer Token
  - Jenkins: Basic Auth + CSRF crumb 自動處理
- **測試框架**: pytest + pytest-asyncio
