# 擴充需求一：支援 WARNING

> 對應投影片：Part 3｜擴充需求（WARNING SDD Prompt）

新需求進來，照 SDD 走一輪。注意：先別動程式碼。

---

我們要替 Log Error Summarizer 新增 WARNING 支援。

請先不要修改程式碼。請依照 SDD 流程走完前半段：

1. 更新 specs/log-error-summarizer.md，把 WARNING 的解析規則寫進去
2. 更新 specs/acceptance-criteria.md，新增 AC-W1、AC-W2…
3. 說明需要新增哪些 pytest（先列名單，不要動實作）
4. 提出實作計畫（哪些 function 要改、哪些檔案會被動到）
5. 完成後停下來回報，不要修改 `src/`，不要修改既有 `tests/test_log_summarizer.py`

需求重點：

- WARNING 不影響 PASS / FAIL 狀態
- summary.md 要獨立統計 warning 數量，並列出每一條 warning 對應的 test_name 與 message
- summary.csv 要保留既有欄位，並新增 `warning_message` 欄位
- 不要新增 `output/warnings.md`；本次 WARNING 明細放在 `summary.md` 與 `summary.csv`

請使用以下固定設計決策，不要自行改成其他設計：

1. WARNING 可以同時出現在 PASS 與 FAIL 後方，且不改變 PASS / FAIL 狀態
2. 一個 test 可以有多個 WARNING，每一條 WARNING 都要獨立記錄
3. `summary.csv` 採「一個 event 一列」：
   - error event：填 `error_category` / `error_message`，`warning_message` 留空
   - warning event：`error_category` 填 `None`，`error_message` 留空，`warning_message` 填 warning 內容
4. 第一版 WARNING 不需要 severity
5. 如果 WARNING 沒有對應 test，`file` 保留原 log 檔名，`test_name` 填 `system`

請把以上五點寫進 spec，並把 acceptance criteria 寫成可直接轉成 pytest 的條目。
