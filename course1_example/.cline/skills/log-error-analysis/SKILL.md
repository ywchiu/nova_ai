---
name: log-error-analysis
description: Analyze test logs, simulation logs, build logs, and regression logs. Use when parsing .log files, summarizing failures, classifying errors, counting warnings, or grouping repeated error signatures.
---

# Log Error Analysis Skill

## When to use

Use this skill when the task involves analyzing test logs, simulation logs, build logs, or regression logs from engineering pipelines. Load this skill before parsing or summarizing any `.log` content.

## Goal

Turn raw engineering logs into structured summaries that help engineers identify failures, warnings, repeated error patterns, and suggested next checks.

## Supported log markers

- `[PASS] test_name`
- `[FAIL] test_name`
- `ERROR: message`
- `WARNING: message`
- `FATAL: message`
- `TIMEOUT: message`

A WARNING after `[PASS]` does not change the result.

## Error Classification

Match against the message body in this order. First match wins.

| Type | Keywords (case-insensitive) |
|------|-----------------------------|
| Timeout | `timeout`, `timed out`, `waiting for`, `simulation timeout` |
| Data mismatch | `expected`, `got`, `mismatch`, `compare failed` |
| Fatal | `fatal`, `crash`, `segmentation fault` |
| Environment | `file not found`, `permission denied`, `license checkout failed`, `license server not responding` |
| Unknown | use when no rule matches |

## Warning Handling

- Warnings should not change PASS / FAIL status.
- Warnings should be counted independently from failures.
- Warnings should appear in the Markdown report under a `## Warnings` section.
- A warning is associated with the nearest preceding active test case in the same file.

## Repeated Error Signatures

A repeated error signature is defined as:

- same normalized error message
- appears in at least two failed tests

Normalization rules:

1. Lowercase
2. Strip leading and trailing whitespace
3. Collapse multiple whitespaces into one
4. Remove `ERROR:`, `FATAL:`, `TIMEOUT:` prefixes

The report should include for each signature:

- normalized error message
- count
- list of related test names

## Report Guidance

Engineers usually read the report in this order, so structure the Markdown to match:

1. Overview
2. Failure Groups
3. Repeated Error Signatures
4. Warnings
5. Suggested Next Checks

A good summary helps an engineer triage in under 2 minutes. Cut prose, keep structure.
