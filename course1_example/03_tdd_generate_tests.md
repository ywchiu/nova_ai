# TDD：把驗收條件轉成 pytest

> 對應投影片：Part 2｜TDD（把 AC 轉成 pytest）

驗收條件確定之後，用這段先把測試補齊（先 RED）。

---

請根據 specs/acceptance-criteria.md，先產生 pytest 測試。

要求：

1. 測試檔放在 tests/test_log_summarizer.py
2. 先不要實作功能，不要建立 `src/log_summarizer.py`。我希望這時候執行 pytest 會看到測試失敗，但失敗原因要是「找不到對應的 module/function」，不是 syntax error
3. 每一條 Acceptance Criteria 至少要對應一個測試
4. 測試名稱要清楚描述行為，例如：
   - test_parse_pass_line_records_pass_result
   - test_fail_without_error_uses_unknown_error
   - test_empty_log_generates_zero_count_summary
   - test_multiple_logs_are_aggregated
5. 測試資料一律使用 tmp_path，不可以直接讀寫 sample_logs/
6. 採用 Arrange / Act / Assert 三段式結構，留空行區分
7. 測試一律從 `src.log_summarizer` 匯入 function，例如：
   - `from src.log_summarizer import parse_log_file, classify_error, summarize_logs`
8. 測試呼叫 `summarize_logs` 時請固定使用這個 API：
   - `summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")`

第一批至少要包含這些情境：

- 解析 [PASS] test_name
- 解析 [FAIL] test_name 後面接 ERROR
- Timeout 分類
- Data mismatch 分類
- 空 log 檔
- FAIL 但沒有 ERROR
- 多個 log 檔合併統計
- summary.md 與 summary.csv 都會被產生
- summary.md 一定包含 `Suggested Next Checks` 區段，方便工程師知道下一步該查什麼

寫完之後請執行一次 pytest，把失敗訊息貼出來給我看，再決定要不要進實作。

如果執行 pytest 時出現 `No module named pytest`，請先執行：

```bash
python -m pip install pytest
```

然後重跑 pytest。
