# Course 2 範例包｜投影片可貼用案例

對應最終版投影片：

- `slides/20260518 從 Vibe Coding 到 Agentic Engineering：AI 原生開發流程實戰.pptx`
- `slides/20260518 從 Vibe Coding 到 Agentic Engineering：AI 原生開發流程實戰.pdf`

這個資料夾放的是課堂中可直接貼到 Cline / Roo / Claude Code 類工具示範的案例。前兩個對應前段 Cline 基本操作與 test plan，後三個對應第 110 頁之後的 FIFO 流程再造案例。

## 檔案地圖

| 檔案 | 主軸案例 | 對應投影片 | 什麼時候講 |
|---|---|---:|---|
| `01_bug_report_cline.md` | Bug Report：先整理可重現資訊，不直接改 code | 27-30 | 第 27 頁「以 Bug Report 為例」後貼 prompt；第 28 頁對照 Vibe Coding 風險 |
| `02_test_plan_draft.md` | Test Plan：把規格片段整理成測試初稿 | 59-65 | 第 59 頁貼 prompt；第 62-65 頁對照輸出格式、few-shot、角色設定 |
| `03_fifo_issue_agent_contract.md` | FIFO Issue 流程：把模糊需求變成可執行契約 | 110-112 | 講到第 111 頁「Issue 流程新模式」時貼 prompt；第 112 頁對照輸出 |
| `04_fifo_pr_review_checklist.md` | FIFO PR 流程：AI 預審 + 人類確認 | 113-118 | 第 115 頁貼 prompt；第 116/118 頁對照 Review Checklist 與 Summary-first |
| `05_fifo_cicd_failure_triage.md` | FIFO CI/CD 流程：Agent 進入回饋迴圈 | 119-121 | 第 120 頁貼 prompt；第 121 頁講 Agent 與 CI 雙向流程 |

## Fixture 資料

FIFO 三個範例都可以直接整段貼到 Cline。若課堂上想示範 `@file` 或 MCP 不通時的 fallback，可改用以下獨立 fixture：

| Fixture | 對應範例 | 用途 |
|---|---|---|
| `fixtures/issue_draft.txt` | `03_fifo_issue_agent_contract.md` | 模糊 Issue 草稿 |
| `fixtures/fifo_overflow_pr.diff` | `04_fifo_pr_review_checklist.md` | 模擬 PR diff |
| `fixtures/jenkins_failure.log` | `05_fifo_cicd_failure_triage.md` | 模擬 Jenkins 失敗 log |

建議在 Cline 使用 Plan 模式先跑一次，並在 prompt 裡保留「不要修改檔案、不要呼叫 MCP / 外部系統」的限制。

## 講法建議

1. Bug Report 與 Test Plan 先用來建立「不要直接改、先整理 artifact」的心智模型。
2. FIFO 三個案例再銜接 Issue、PR、CI/CD 流程再造。
3. 每個案例都要保留人類決策點：bug 不直接修、test plan 不腦補規格、Issue 不自動定需求、PR 不自動 merge、CI 不自動 deploy。
4. 現場示範時先用範例文字跑一次，再請學員替換成自己團隊的 bug report、規格片段、Issue、PR diff 或 CI log。
