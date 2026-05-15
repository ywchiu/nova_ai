# SDD：從規格產出驗收條件

> 對應投影片：Part 1｜SDD（AC Prompt）

spec 寫完之後，用這段把規格轉成可被測試驗證的條列。

---

請根據 specs/log-error-summarizer.md，整理出 Acceptance Criteria。

每一條 Acceptance Criteria 都要符合三個原則：

1. 可被測試驗證（pytest 能跑出對錯）
2. 有明確輸入與預期輸出
3. 不依賴主觀判斷

請輸出到 specs/acceptance-criteria.md，使用以下格式：

```
## AC1: 一句話描述條件
Given <情境>
When <動作>
Then <預期結果>
```

至少要涵蓋以下行為：

- 解析 [PASS] 與 [FAIL] 各自的紀錄結構
- ERROR / FATAL / TIMEOUT 訊息的分類規則
- 一個 test 沒有對應 ERROR 時的行為
- 空 log 檔的行為
- 多個 log 檔合併統計
- summary.md 與 summary.csv 各自需要的欄位
- sample_logs/ 一律不修改（這條會變成 Rules）

請不要另外加入版本資訊、作者、建立日期或固定範例日期。這份文件只需要 Acceptance Criteria。

寫完後請停下來等我確認。
