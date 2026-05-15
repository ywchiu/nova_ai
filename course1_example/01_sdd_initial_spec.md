# SDD：建立第一份規格

> 對應投影片：Part 1｜SDD（不要先寫 Code，先建立 Spec）

把這段整個複製到 Cline。它會請 AI 先寫規格、暫時不要碰程式碼。

---

我們要開發一個 Log Error Summarizer。

請先不要寫程式碼。
請先建立 specs/log-error-summarizer.md。

Spec 需要包含以下七個段落：

1. Problem Statement：這個工具解決什麼問題
2. Input Format：可以假設的輸入格式（哪些目錄、哪些檔名規則、哪些訊息標記）
3. Output Format：報告與資料檔的固定格式
4. Error Classification Rules：錯誤怎麼分類（Timeout、Data mismatch、Fatal、Environment、Unknown）
5. Acceptance Criteria：條列式的可驗收條件
6. Edge Cases：空檔、格式錯誤、缺少 ERROR 訊息等
7. Non-goals：這一版明確不做的事

第一版需求：

- 讀取 sample_logs/ 目錄底下所有 .log 檔案
- 解析 [PASS] 與 [FAIL] 兩種測試結果
- 抓取 ERROR、FATAL、TIMEOUT 三種錯誤訊息
- 依錯誤訊息分類
- 輸出 output/summary.md 與 output/summary.csv

Non-goals：

- 不解析完整 EDA tool 專有格式
- 不判斷真正 root cause
- 不修改原始 log
- 不自動回寫 CI 或 Issue
- 不引入非必要外部套件

請不要另外加入版本資訊、作者、建立日期或固定範例日期。這份 spec 只需要上面七個段落。

寫完 spec 後，請先停下來，讓我看過一輪再繼續。
