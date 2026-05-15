from __future__ import annotations

import csv

from src.log_summarizer import classify_error, parse_log_file, summarize_logs


def test_parse_pass_line_records_pass_result(tmp_path):
    """AC1: PASS records are parsed with their test name."""
    log_file = tmp_path / "smoke.log"
    log_file.write_text("2026-05-10 09:00:01 [PASS] test_boot_sequence\n", encoding="utf-8")

    parsed = parse_log_file(log_file)

    assert parsed["tests"][0]["test_name"] == "test_boot_sequence"
    assert parsed["tests"][0]["status"] == "PASS"


def test_parse_fail_line_with_error_records_error_event(tmp_path):
    """AC2: FAIL records keep the following error message."""
    log_file = tmp_path / "smoke.log"
    log_file.write_text(
        "2026-05-10 09:00:01 [FAIL] test_config_load\n"
        "2026-05-10 09:00:02 ERROR: file not found: config/default.yaml\n",
        encoding="utf-8",
    )

    parsed = parse_log_file(log_file)

    assert parsed["events"][0]["test_name"] == "test_config_load"
    assert parsed["events"][0]["error_category"] == "Environment"


def test_timeout_error_is_classified():
    """AC3: TIMEOUT-like messages are classified as Timeout."""
    assert classify_error("simulation timeout waiting for ack") == "Timeout"


def test_data_mismatch_error_is_classified():
    """AC4: expected/got messages are classified as Data mismatch."""
    assert classify_error("expected 0x3A but got 0x00") == "Data mismatch"


def test_empty_log_generates_zero_count_summary(tmp_path):
    """AC5: Empty log files still produce reports with zero totals."""
    (tmp_path / "empty.log").write_text("", encoding="utf-8")

    result = summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")

    assert result["total_tests"] == 0
    assert "Total tests: 0" in (tmp_path / "output" / "summary.md").read_text(encoding="utf-8")


def test_fail_without_error_uses_none_category(tmp_path):
    """AC6: FAIL without an error marker is emitted as category None."""
    (tmp_path / "missing_error.log").write_text("2026-05-10 09:00:01 [FAIL] test_no_marker\n", encoding="utf-8")

    summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")

    rows = list(csv.DictReader((tmp_path / "output" / "summary.csv").open(encoding="utf-8")))
    assert rows[0]["test_name"] == "test_no_marker"
    assert rows[0]["error_category"] == "None"


def test_multiple_logs_are_aggregated(tmp_path):
    """AC7: Multiple .log files are summarized together."""
    (tmp_path / "a.log").write_text("2026-05-10 09:00:01 [PASS] test_a\n", encoding="utf-8")
    (tmp_path / "b.log").write_text("2026-05-10 09:00:01 [FAIL] test_b\nERROR: license server not responding\n", encoding="utf-8")

    result = summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")

    assert result["total_tests"] == 2
    assert result["passed"] == 1
    assert result["failed"] == 1


def test_summary_md_and_summary_csv_are_generated(tmp_path):
    """AC8: Markdown and CSV reports are both generated."""
    (tmp_path / "run.log").write_text("2026-05-10 09:00:01 [PASS] test_ok\n", encoding="utf-8")

    summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")

    assert (tmp_path / "output" / "summary.md").exists()
    assert (tmp_path / "output" / "summary.csv").exists()


def test_summary_md_contains_suggested_next_checks(tmp_path):
    """AC9: Markdown report always includes next-check guidance."""
    (tmp_path / "run.log").write_text("2026-05-10 09:00:01 [PASS] test_ok\n", encoding="utf-8")

    summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")

    assert "## Suggested Next Checks" in (tmp_path / "output" / "summary.md").read_text(encoding="utf-8")


def test_warning_events_do_not_change_pass_fail_status(tmp_path):
    """AC-W1: WARNING is counted independently and does not change PASS."""
    (tmp_path / "warning.log").write_text(
        "2026-05-10 09:00:01 [PASS] test_boot_sequence\n"
        "2026-05-10 09:00:02 WARNING: boot took 8.2s\n",
        encoding="utf-8",
    )

    result = summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")

    assert result["passed"] == 1
    assert result["failed"] == 0
    assert result["warning_count"] == 1


def test_repeated_error_signatures_are_grouped_in_summary_md(tmp_path):
    """AC-R1: Repeated normalized error messages are grouped."""
    (tmp_path / "i2c.log").write_text(
        "2026-05-10 10:00:01 [FAIL] test_i2c_read\n"
        "2026-05-10 10:00:02 ERROR: expected 0x3A but got 0x00\n"
        "2026-05-10 10:01:01 [FAIL] test_i2c_write\n"
        "2026-05-10 10:01:02 ERROR: expected 0x3A but got 0x00\n",
        encoding="utf-8",
    )

    summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")

    summary = (tmp_path / "output" / "summary.md").read_text(encoding="utf-8")
    assert "## Repeated Error Signatures" in summary
    assert "expected 0x3a but got 0x00" in summary
    assert "test_i2c_read" in summary
    assert "test_i2c_write" in summary


def test_single_occurrence_error_is_not_listed_as_repeated_signature(tmp_path):
    """AC-R2: Single-occurrence messages are not listed as repeated signatures."""
    (tmp_path / "mixed.log").write_text(
        "2026-05-10 10:00:01 [FAIL] test_a\n"
        "2026-05-10 10:00:02 ERROR: expected 0x3A but got 0x00\n"
        "2026-05-10 10:01:01 [FAIL] test_b\n"
        "2026-05-10 10:01:02 ERROR: expected 0x3A but got 0x00\n"
        "2026-05-10 10:02:01 [FAIL] test_license_checkout\n"
        "2026-05-10 10:02:02 ERROR: license server not responding\n",
        encoding="utf-8",
    )

    summarize_logs(input_dir=tmp_path, output_dir=tmp_path / "output")

    repeated_section = (tmp_path / "output" / "summary.md").read_text(encoding="utf-8").split("## Repeated Error Signatures", 1)[1]
    assert "license server not responding" not in repeated_section
