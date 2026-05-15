# /summarize-logs

Run the log summarizer end-to-end and report results.

0. Prepare fixture logs if needed. If `sample_logs/` does not exist and `course1_example/sample_logs/` exists, copy `course1_example/sample_logs/` to `sample_logs/` once. After that, treat `sample_logs/` as read-only. If neither path exists, stop and report the missing fixture.
1. Inspect `sample_logs/`. List files and sizes. Note any unexpected file types.
2. Run the summarizer. Prefer the module's documented CLI entrypoint if one exists. If there is no CLI entrypoint yet, run:

   ```bash
   python - <<'PY'
   from src.log_summarizer import summarize_logs

   summarize_logs("sample_logs", "output")
   PY
   ```

3. Generate `output/summary.md`. Confirm file exists and includes Overview, Failure Groups, and Suggested Next Checks.
4. Generate `output/summary.csv`. Confirm file exists with the expected base columns.
5. Validate counts. Cross-check warning and repeated-signature counts only when the implementation reports those fields.
6. Run pytest. If the project is not intentionally in a RED phase, confirm all tests pass.
7. Report generated files, test totals, top repeated signatures, and anything unusual.

Do not modify any file under `sample_logs/`.
