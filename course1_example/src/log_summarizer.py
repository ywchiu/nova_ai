from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TEST_RE = re.compile(r"\[(PASS|FAIL)\]\s+([A-Za-z0-9_.:-]+)")
ERROR_RE = re.compile(r"\b(ERROR|FATAL|TIMEOUT):\s*(.*)$", re.IGNORECASE)
WARNING_RE = re.compile(r"\bWARNING:\s*(.*)$", re.IGNORECASE)


def classify_error(message: str) -> str:
    """Classify an error message into the course's fixed categories."""
    body = message.lower()
    if any(keyword in body for keyword in ("timeout", "timed out", "waiting for", "simulation timeout")):
        return "Timeout"
    if any(keyword in body for keyword in ("expected", "got", "mismatch", "compare failed")):
        return "Data mismatch"
    if any(keyword in body for keyword in ("fatal", "crash", "segmentation fault")):
        return "Fatal"
    if any(keyword in body for keyword in ("file not found", "permission denied", "license checkout failed", "license server not responding")):
        return "Environment"
    return "Unknown"


def normalize_error_signature(message: str) -> str:
    """Normalize an error message for repeated signature grouping."""
    body = re.sub(r"^\s*(ERROR|FATAL|TIMEOUT):\s*", "", message, flags=re.IGNORECASE)
    body = re.sub(r"\s+", " ", body.strip().lower())
    return body


def parse_log_file(path: str | Path) -> dict[str, Any]:
    """Parse one .log file into test records and report events."""
    log_path = Path(path)
    tests: dict[str, dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    active_test = "system"

    for line_number, raw_line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), start=1):
        test_match = TEST_RE.search(raw_line)
        if test_match:
            status, test_name = test_match.groups()
            active_test = test_name
            tests[test_name] = {
                "file": log_path.name,
                "test_name": test_name,
                "status": status,
                "line_number": line_number,
                "has_error": False,
            }
            continue

        error_match = ERROR_RE.search(raw_line)
        if error_match:
            marker, message = error_match.groups()
            normalized_message = message.strip()
            if active_test in tests:
                tests[active_test]["has_error"] = True
            events.append(
                {
                    "event_type": "error",
                    "file": log_path.name,
                    "test_name": active_test,
                    "error_category": classify_error(normalized_message if marker.upper() != "TIMEOUT" else f"TIMEOUT: {normalized_message}"),
                    "error_message": normalized_message,
                    "warning_message": "",
                    "line_number": line_number,
                }
            )
            continue

        warning_match = WARNING_RE.search(raw_line)
        if warning_match:
            events.append(
                {
                    "event_type": "warning",
                    "file": log_path.name,
                    "test_name": active_test,
                    "error_category": "None",
                    "error_message": "",
                    "warning_message": warning_match.group(1).strip(),
                    "line_number": line_number,
                }
            )

    for test in tests.values():
        if test["status"] == "FAIL" and not test["has_error"]:
            events.append(
                {
                    "event_type": "error",
                    "file": test["file"],
                    "test_name": test["test_name"],
                    "error_category": "None",
                    "error_message": "",
                    "warning_message": "",
                    "line_number": test["line_number"],
                }
            )

    return {"file": log_path.name, "tests": list(tests.values()), "events": events}


def summarize_logs(input_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    """Summarize all .log files from input_dir into summary.md and summary.csv."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    parsed_logs = [parse_log_file(path) for path in sorted(input_path.glob("*.log"))]
    tests = [test for parsed in parsed_logs for test in parsed["tests"]]
    events = [event for parsed in parsed_logs for event in parsed["events"]]
    error_events = [event for event in events if event["event_type"] == "error"]
    warning_events = [event for event in events if event["event_type"] == "warning"]

    category_counts = Counter(event["error_category"] for event in error_events)
    repeated_signatures = _find_repeated_signatures(error_events)

    _write_summary_md(output_path / "summary.md", tests, error_events, warning_events, category_counts, repeated_signatures)
    _write_summary_csv(output_path / "summary.csv", events)

    return {
        "total_tests": len(tests),
        "passed": sum(1 for test in tests if test["status"] == "PASS"),
        "failed": sum(1 for test in tests if test["status"] == "FAIL"),
        "error_count": len(error_events),
        "warning_count": len(warning_events),
        "repeated_signature_count": len(repeated_signatures),
    }


def _find_repeated_signatures(error_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for event in error_events:
        if not event["error_message"]:
            continue
        signature = normalize_error_signature(event["error_message"])
        grouped[signature].append(event["test_name"])

    repeated = []
    for signature, test_names in sorted(grouped.items()):
        if len(test_names) >= 2:
            repeated.append({"signature": signature, "count": len(test_names), "test_names": sorted(test_names)})
    return repeated


def _write_summary_md(
    path: Path,
    tests: list[dict[str, Any]],
    error_events: list[dict[str, Any]],
    warning_events: list[dict[str, Any]],
    category_counts: Counter[str],
    repeated_signatures: list[dict[str, Any]],
) -> None:
    passed = sum(1 for test in tests if test["status"] == "PASS")
    failed = sum(1 for test in tests if test["status"] == "FAIL")
    lines = [
        "# Log Error Summary",
        "",
        "## Overview",
        "",
        f"- Total tests: {len(tests)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Error events: {len(error_events)}",
        f"- Warning events: {len(warning_events)}",
        "",
        "## Failure Groups",
        "",
    ]

    if category_counts:
        for category, count in sorted(category_counts.items()):
            lines.append(f"- {category}: {count}")
    else:
        lines.append("- No failures found.")

    if repeated_signatures:
        lines.extend(["", "## Repeated Error Signatures", ""])
        for item in repeated_signatures:
            joined_tests = ", ".join(item["test_names"])
            lines.append(f"- `{item['signature']}`: {item['count']} occurrences ({joined_tests})")

    if warning_events:
        lines.extend(["", "## Warnings", ""])
        for event in warning_events:
            lines.append(f"- {event['file']}::{event['test_name']}: {event['warning_message']}")

    lines.extend(["", "## Suggested Next Checks", ""])
    if not error_events:
        lines.append("- No blocker found in current logs.")
    else:
        suggestions = {
            "Timeout": "Check simulation runtime, waits, and external service response time.",
            "Data mismatch": "Compare expected data setup against observed values.",
            "Fatal": "Inspect crash logs and recent low-level code changes.",
            "Environment": "Check files, permissions, and license service availability.",
            "Unknown": "Inspect raw log context around the failure line.",
            "None": "Add error markers near failing tests to improve triage.",
        }
        for category in sorted(category_counts):
            lines.append(f"- {category}: {suggestions.get(category, suggestions['Unknown'])}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary_csv(path: Path, events: list[dict[str, Any]]) -> None:
    fieldnames = ["file", "test_name", "error_category", "error_message", "line_number", "warning_message"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for event in events:
            writer.writerow({field: event[field] for field in fieldnames})
