# MCP：Issue 驅動開發指令

> 對應投影片：Part 7｜MCP（企業版情境 Prompt）

當你已經把 Jira / GitHub / CI / Git 透過 MCP 接上 Cline 之後，這段 prompt 會把整個流程串起來。

前提：MCP 連線已設定好，Cline 能讀 Issue、能讀 CI artifact、能讀 repo diff。

如果是在本機課堂測試、MCP 尚未接好，請不要編造 Issue、CI log 或 PR 狀態。請先列出缺少哪些 MCP tool，並改用「dry-run plan」說明你會怎麼執行。

---

請使用 MCP 工具完成以下任務：

1. 取得 Issue #128 的需求內容（用 issue tracker 的 MCP tool）
2. 讀取最近一次 CI run 的失敗 log（用 ci 的 MCP tool）
3. 使用 /sdd-feature workflow 開發功能
4. 開發完成後執行 pytest
5. 產生一段可以貼回 Issue 的開發摘要

整個過程要遵守的限制：

- 不讀取任何未授權專案的資料
- 不修改 sample_logs/ 底下任何檔案
- 寫入 Issue 之前先把草稿給我看，我確認再寫
- 任何 PR comment 都要先列出來等我確認
- 不要嘗試讀取 secrets、license key、production config

如果使用者已開啟 auto-act，可以連續完成讀取、分析、修改本機檔案與測試步驟；每一步仍要在最後摘要列出結果。任何外部寫入（Issue comment、PR comment、push、merge、部署）都必須先停下來給草稿並等待確認。
