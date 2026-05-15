# TDD：最小實作讓第一版測試通過

> 對應投影片：Part 2｜TDD（GREEN：最小實作）

跑完 `03_tdd_generate_tests.md` 之後，用這段讓 Cline 進入最小實作。

---

請根據 `specs/log-error-summarizer.md`、`specs/acceptance-criteria.md` 與 `tests/test_log_summarizer.py`，實作第一版 Log Error Summarizer。

要求：

1. 只實作讓目前測試通過所需的最小功能，不要加入 WARNING 或 Repeated Error Signatures
2. 主要程式放在 `src/log_summarizer.py`
3. 如果 `src/` 目錄不存在，請先建立它；如果 `src/__init__.py` 不存在，請建立空檔案
4. 使用 Python standard library，不要新增外部套件
5. 保留可測試的 function，至少包含：
   - `parse_log_file(path)`
   - `classify_error(message)`
   - `summarize_logs(input_dir, output_dir)`
6. 測試會使用 `from src.log_summarizer import ...`，所以不要把主程式放到專案根目錄的 `log_summarizer.py`
7. `summarize_logs` 要支援以下呼叫方式：
   - `summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")`
8. `summarize_logs` 要產生：
   - `output/summary.md`
   - `output/summary.csv`
9. `summary.md` 至少要包含：
   - `Overview` 或 `Test Results Overview`
   - `Failure Groups` 或 `Error Summary`
   - `Suggested Next Checks`
10. `Suggested Next Checks` 要依錯誤分類輸出簡短行動建議；如果沒有錯誤，仍要輸出一行表示目前沒有 blocker。
11. `classify_error("license server not responding")` 要回傳 `Environment`
12. 如果 log 內有 `[FAIL] test_name`，但後面沒有 `ERROR` / `FATAL` / `TIMEOUT` 行，也要在 `summary.csv` 產生一列：
   - `test_name` 是該 failed test
   - `error_category` 是 `None`
   - `error_message` 可以是空字串
13. 不可以修改 `sample_logs/`
14. 不可以弱化或刪除既有測試
15. 如果需要建立檔案，請先確認父目錄存在，不要直接對不存在的目錄執行 `touch`

完成後請執行：

```bash
python -m pytest -q
```

回報：

- 修改了哪些檔案
- pytest 結果
- 第一版還沒支援哪些功能
