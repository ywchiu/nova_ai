# Workflow：/summarize-logs

> 對應投影片：Part 6｜Workflows（/summarize-logs）

把下面內容存到 `.clinerules/workflows/summarize-logs.md`。

在 Cline 對話輸入 `/summarize-logs` 觸發；如果 autocomplete 顯示 `/summarize-logs.md`，就選它。

---

# /summarize-logs

Run the log summarizer end-to-end and report results.

0. **Prepare fixture logs if needed.** If `sample_logs/` does not exist and `course1_example/sample_logs/` exists, copy `course1_example/sample_logs/` to `sample_logs/` once. After that, treat `sample_logs/` as read-only. If neither path exists, stop and report the missing fixture.
1. **Inspect sample_logs/.** List files and sizes. Note any unexpected file types.
2. **Run the summarizer.** Prefer the module's documented CLI entrypoint if one exists. If there is no CLI entrypoint yet, run this Python snippet instead:

   ```bash
   python - <<'PY'
   from src.log_summarizer import summarize_logs

   summarize_logs("sample_logs", "output")
   PY
   ```
3. **Generate output/summary.md.** Confirm file exists and includes Overview, Failure Groups, and Suggested Next Checks. If the current implementation supports warnings and warning data exists, confirm the Warnings section exists. If the current implementation supports repeated signatures and repeated data exists, confirm the Repeated Error Signatures section exists.
4. **Generate output/summary.csv.** Confirm file exists with the expected base columns. If warning support is implemented, confirm `warning_message` is appended without renaming the base columns.
5. **Validate counts.** Cross-check warning_count and repeated_signature_count only when the current implementation reports those fields. If the feature is not implemented yet, explicitly report it as not applicable instead of failing the workflow.
6. **Run pytest.** If the project is not intentionally in a RED phase, confirm all tests pass. If there are known RED tests from an unfinished TDD step, run pytest, report the failing test names, and explicitly say they are expected pending implementation.
7. **Report.** Output a short report listing:
   - Generated files (paths)
   - Test totals (pass/fail/warnings)
   - Top 3 repeated signatures (if any)
   - Anything that looked unusual

Do not modify any file under sample_logs/.
