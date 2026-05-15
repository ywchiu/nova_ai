# Acceptance Criteria

## AC1: PASS records are parsed
Given a log file with `[PASS] test_boot_sequence`
When the parser reads the file
Then it records `test_boot_sequence` with status `PASS`

## AC2: FAIL records preserve error context
Given a log file with `[FAIL] test_config_load` followed by `ERROR: file not found: config/default.yaml`
When the parser reads the file
Then it records an error event for `test_config_load` with category `Environment`

## AC3: Timeout classification
Given an error message containing `simulation timeout`
When `classify_error` is called
Then it returns `Timeout`

## AC4: Data mismatch classification
Given an error message containing `expected` and `got`
When `classify_error` is called
Then it returns `Data mismatch`

## AC5: Empty log file
Given an empty `.log` file
When the summarizer runs
Then it generates reports with zero total tests

## AC6: FAIL without error marker
Given a failed test with no following ERROR, FATAL, or TIMEOUT line
When the summarizer writes `summary.csv`
Then it includes a row for that test with `error_category` set to `None`

## AC7: Multiple logs are aggregated
Given two `.log` files in the input directory
When the summarizer runs
Then one report contains totals from both files

## AC8: Required report files
Given any valid input directory
When the summarizer runs
Then it writes both `summary.md` and `summary.csv`

## AC9: Suggested next checks
Given any valid input directory
When the summarizer writes `summary.md`
Then the report includes `## Suggested Next Checks`

## AC-W1: Warning does not change test status
Given a PASS test followed by a WARNING
When the summarizer runs
Then the test remains PASS and warning count increases

## AC-W2: Warning CSV event format
Given a WARNING line
When the summarizer writes `summary.csv`
Then it emits a row with `warning_message` populated, `error_category` set to `None`, and `error_message` empty

## AC-R1: Repeated error signatures are grouped
Given two failed tests with the same normalized error message
When the summarizer writes `summary.md`
Then `## Repeated Error Signatures` lists the message, count, and related tests

## AC-R2: Single occurrence is not repeated
Given an error message that appears only once
When repeated signatures are reported
Then that message is not listed in the repeated-signature section
