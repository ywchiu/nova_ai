# Log Error Summarizer Spec

## Problem Statement

Regression logs are often long, noisy, and spread across multiple files. This tool scans engineering `.log` files and creates a compact summary so engineers can quickly see which tests failed, how failures are grouped, which warnings appeared, and what to check next.

## Input Format

- Input logs live under `sample_logs/` or another caller-provided directory.
- Only files ending in `.log` are parsed.
- Supported test result markers:
  - `[PASS] test_name`
  - `[FAIL] test_name`
- Supported message markers:
  - `ERROR: message`
  - `FATAL: message`
  - `TIMEOUT: message`
  - `WARNING: message`
- A message is associated with the nearest preceding test in the same file. If a warning has no preceding test, it is associated with `system`.

## Output Format

The tool writes reports under `output/` or another caller-provided output directory.

- `summary.md` contains:
  - Overview
  - Failure Groups
  - Repeated Error Signatures, only when repeated signatures exist
  - Warnings, only when warnings exist
  - Suggested Next Checks
- `summary.csv` contains one event per row with these columns:
  - `file`
  - `test_name`
  - `error_category`
  - `error_message`
  - `line_number`
  - `warning_message`

For an error event, `error_category` and `error_message` are populated and `warning_message` is empty. For a warning event, `warning_message` is populated, `error_category` is `None`, and `error_message` is empty.

## Error Classification Rules

Messages are classified in this order, first match wins:

1. Timeout: `timeout`, `timed out`, `waiting for`, `simulation timeout`
2. Data mismatch: `expected`, `got`, `mismatch`, `compare failed`
3. Fatal: `fatal`, `crash`, `segmentation fault`
4. Environment: `file not found`, `permission denied`, `license checkout failed`, `license server not responding`
5. Unknown: no rule matches

## Acceptance Criteria

- The parser records `[PASS]` and `[FAIL]` test names.
- The parser captures `ERROR`, `FATAL`, and `TIMEOUT` messages after failed tests.
- A failed test without an error marker appears in `summary.csv` with `error_category` set to `None`.
- Empty `.log` files produce valid reports with zero totals.
- Multiple `.log` files are aggregated into one report.
- `summary.md` and `summary.csv` are both generated.
- `summary.md` always includes Suggested Next Checks.
- Warnings do not change PASS / FAIL status and are counted independently.
- Repeated error signatures are listed only when the normalized message appears at least twice.
- `sample_logs/` is never modified by the tool.

## Edge Cases

- Empty input directory: generate reports with zero totals.
- Empty log file: count zero tests and continue.
- FAIL without ERROR / FATAL / TIMEOUT: include a row with category `None`.
- WARNING before any test: attach it to `system`.
- Multiple WARNING lines after one test: emit one row per warning.
- Duplicate error text across multiple tests: group as a repeated signature.

## Non-goals

- Do not parse complete EDA tool formats.
- Do not determine the true root cause automatically.
- Do not modify original logs.
- Do not post issue comments, open PRs, or update CI systems.
- Do not require external Python packages.

## WARNING Support

WARNING lines are parsed independently from PASS / FAIL status. A WARNING can appear after either a PASS or FAIL test and does not change that test's status. Each warning is emitted as a separate CSV event and appears under `## Warnings` in `summary.md`.

## Repeated Error Signatures

Repeated signatures are detected from error events. A signature is included only when the normalized message appears in at least two failed tests.

Normalization rules:

1. Lowercase the message.
2. Strip leading and trailing whitespace.
3. Collapse repeated whitespace into one space.
4. Remove `ERROR:`, `FATAL:`, and `TIMEOUT:` prefixes.
