# Course 2 範例包｜投影片可貼用案例

對應最終版投影片：

- `slides/20260518 從 Vibe Coding 到 Agentic Engineering：AI 原生開發流程實戰.pptx`
- `slides/20260518 從 Vibe Coding 到 Agentic Engineering：AI 原生開發流程實戰.pdf`

這個資料夾放的是課堂中可直接貼到 Cline / Roo / Claude Code 類工具示範的案例。前兩個對應前段 Cline 基本操作與 test plan，後三個對應第 110 頁之後的 FIFO 流程再造案例。

## 白話版情境總覽

這五個範例不是要教大家 IC 設計細節，而是示範「不要把模糊問題直接丟給 AI 改 code」。你可以把它想成一般軟體開發流程：

| 範例 | 白話理解 | AI 在這裡做什麼 |
|---|---|---|
| Bug Report | 有人只說「畫面偶爾壞掉，幫我修」，但沒有說怎麼重現 | 先把現象、缺少資訊、要看哪些證據整理出來 |
| Test Plan | 需求文件只有幾句話，還不能直接寫測試 | 先把可測的行為列成表格，也標出哪些規格不清楚 |
| FIFO Issue | 有人只說「某個佇列滿了以後行為怪怪的」 | 把一句話整理成可討論、可驗收的 Issue |
| FIFO PR Review | 有人改了一段跟佇列滿載有關的程式 | 先幫 reviewer 找風險、缺測試、缺文件的地方 |
| FIFO CI/CD | 自動測試失敗，但 log 很長 | 先整理失敗摘要、證據、可能原因與下一步 |

FIFO 可以先理解成「排隊等處理的資料盒子」。資料一直進來、也會被拿出去；當盒子滿了又有人硬塞資料，就叫 overflow。這時到底要丟掉新資料、暫停寫入、還是允許同時拿出一筆再塞一筆，是設計規格要先決定的事，不應該讓 AI 自己猜。

## 檔案地圖

| 檔案 | 主軸案例 | 對應投影片 | 什麼時候講 |
|---|---|---:|---|
| `01_bug_report_cline.md` | Bug Report：先整理可重現資訊，不直接改 code | 27-30 | 第 27 頁「以 Bug Report 為例」後貼 prompt；第 28 頁對照 Vibe Coding 風險 |
| `02_test_plan_draft.md` | Test Plan：把規格片段整理成測試初稿 | 59-65 | 第 59 頁貼 prompt；第 62-65 頁對照輸出格式、few-shot、角色設定 |
| `03_fifo_issue_agent_contract.md` | FIFO Issue 流程：把模糊需求變成可執行契約 | 110-112 | 講到第 111 頁「Issue 流程新模式」時貼 prompt；第 112 頁對照輸出 |
| `04_fifo_pr_review_checklist.md` | FIFO PR 流程：AI 預審 + 人類確認 | 113-118 | 第 115 頁貼 prompt；第 116/118 頁對照 Review Checklist 與 Summary-first |
| `05_fifo_cicd_failure_triage.md` | FIFO CI/CD 流程：Agent 進入回饋迴圈 | 119-121 | 第 120 頁貼 prompt；第 121 頁講 Agent 與 CI 雙向流程 |

## 範例資料

五個範例都可以直接整段貼到 Cline。若課堂上想示範 `@file`、複製外部 artifact，或 MCP 不通時的 fallback，可改用以下獨立 fixture：

| Fixture | 對應範例 | 用途 |
|---|---|---|
| `fixtures/bug_report.txt` | `01_bug_report_cline.md` | 模擬 bug report 草稿 |
| `fixtures/test_plan_spec.txt` | `02_test_plan_draft.md` | 模擬規格片段 |
| `fixtures/issue_draft.txt` | `03_fifo_issue_agent_contract.md` | 模糊 Issue 草稿 |
| `fixtures/fifo_overflow_pr.diff` | `04_fifo_pr_review_checklist.md` | 模擬 PR diff |
| `fixtures/jenkins_failure.log` | `05_fifo_cicd_failure_triage.md` | 模擬 Jenkins 失敗 log |

建議在 Cline 使用 Plan 模式先跑一次，並在 prompt 裡保留「不要修改檔案、不要呼叫 MCP / 外部系統」的限制。

