# 擴充需求二：重複錯誤訊息

> 對應投影片：Part 3｜擴充需求（Repeated Signature SDD Prompt）

把「同一個錯誤造成多個測試失敗」聚合起來，幫工程師找 root cause。

---

我們要新增 Repeated Error Signatures 功能。

請先不要修改 `src/` 裡的程式碼。請依照 SDD + TDD RED phase 流程：

1. 在 `specs/log-error-summarizer.md` 檔案尾端 append 一段新章節，不要搜尋替換既有內容、不要重寫整份 spec
2. 在 `specs/acceptance-criteria.md` 檔案尾端 append 一段新章節，不要搜尋替換既有內容、不要重寫整份 AC
3. 列出新增的 pytest 測試名稱清單
4. 在 `tests/test_log_summarizer.py` 檔案尾端 append pytest 測試，不要改動既有測試
5. 提出最小實作計畫
6. 執行 pytest，確認新測試會失敗

行為定義：

- 只列出出現次數 >= 2 的 error signature
- 一筆 signature 要包含三個欄位：normalized error message、出現次數、相關的 test_name 列表
- 在 summary.md 加一個 `## Repeated Error Signatures` 章節

normalization 規則（重要，先確定，不要 AI 自己亂寫）：

- 全部轉小寫
- 去除前後空白
- 多個連續空白壓縮成一個
- 移除 `ERROR:` / `FATAL:` / `TIMEOUT:` 等前綴

預期效果：

- 「expected 0x3A but got 0x00」出現在 test_i2c_read 與 test_i2c_write，會被聚合成一筆 signature，count = 2
- 只出現一次的 error message 不會被列入

請在 `tests/test_log_summarizer.py` append 的測試至少包含：

- `test_repeated_error_signatures_are_grouped_in_summary_md`
- `test_single_occurrence_error_is_not_listed_as_repeated_signature`

測試可以直接呼叫既有 `summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")`，讀取 `output/summary.md`，驗證：

- 有 `## Repeated Error Signatures`
- 有 normalized message
- 有 `test_i2c_read` 與 `test_i2c_write`
- 單次出現的 `license server not responding` 不出現在 repeated signature 區段

這一輪是 RED phase：可以修改 `specs/` 和 `tests/test_log_summarizer.py`，但不要修改 `src/log_summarizer.py`。pytest 應該因為 repeated signature 尚未實作而失敗；若 pytest 全部通過，請檢查測試是否真的覆蓋了本需求。

完成後回報：

1. 修改了哪些檔案
2. 新增了哪些 pytest 測試
3. pytest 失敗摘要
