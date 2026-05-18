# Course 2 範例包｜三個主軸案例

對應最終版投影片：

- `slides/20260518 從 Vibe Coding 到 Agentic Engineering：AI 原生開發流程實戰.pptx`
- `slides/20260518 從 Vibe Coding 到 Agentic Engineering：AI 原生開發流程實戰.pdf`

這個資料夾放的是後段「AI 流程再造」的三個主軸案例。每個檔案都可以在講到對應投影片時，直接整段貼到 Cline / Roo / Claude Code 類工具中示範。

## 檔案地圖

| 檔案 | 主軸案例 | 對應投影片 | 什麼時候講 |
|---|---|---:|---|
| `01_issue_agent_contract.md` | Issue 流程：把模糊需求變成可執行契約 | 110-112 | 講到第 111 頁「Issue 流程新模式」時貼 prompt；第 112 頁對照輸出 |
| `02_pr_review_checklist.md` | PR 流程：AI 預審 + 人類確認 | 108, 113-118 | 第 108 頁先講任務；第 115 頁貼 prompt；第 116/118 頁對照輸出 |
| `03_cicd_failure_triage.md` | CI/CD 流程：Agent 進入回饋迴圈 | 119-121 | 第 120 頁貼 prompt；第 121 頁講 Agent 與 CI 雙向流程 |

## Fixture 資料

三個範例都可以直接整段貼到 Cline。若課堂上想示範 `@file` 或 MCP 不通時的 fallback，可改用以下獨立 fixture：

| Fixture | 對應範例 | 用途 |
|---|---|---|
| `fixtures/issue_draft.txt` | `01_issue_agent_contract.md` | 模糊 Issue 草稿 |
| `fixtures/fifo_overflow_pr.diff` | `02_pr_review_checklist.md` | 模擬 PR diff |
| `fixtures/jenkins_failure.log` | `03_cicd_failure_triage.md` | 模擬 Jenkins 失敗 log |

建議在 Cline 使用 Plan 模式先跑一次，並在 prompt 裡保留「不要修改檔案、不要呼叫 MCP / 外部系統」的限制。

## 前置鋪陳頁

正式進三個案例前，可以先用這幾段投影片建立概念：

- 第 88-89 頁：只有 Model vs Model + Harness
- 第 91-96 頁：Harness 五個核心零件
- 第 106-109 頁：AI-Assisted 與 AI-First 的差別，以及每個流程要重問的五題

## 講法建議

1. 先說明：這三個案例不是要讓 AI 取代人，而是把 AI 放進流程裡做「草稿、預審、摘要、證據整理」。
2. 每個案例都要保留人類決策點：Issue 不自動定需求、PR 不自動 merge、CI 不自動 deploy。
3. 現場示範時先用範例文字跑一次，再請學員替換成自己團隊的 Issue、PR diff 或 CI log。
