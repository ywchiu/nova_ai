# Log Error Summary

## Overview

- Total tests: 6
- Passed: 2
- Failed: 4
- Error events: 4
- Warning events: 2

## Failure Groups

- Data mismatch: 2
- Environment: 2

## Repeated Error Signatures

- `expected 0x3a but got 0x00`: 2 occurrences (test_i2c_read, test_i2c_write)

## Warnings

- core_regression.log::test_boot_sequence: boot took 8.2s, above advisory threshold
- i2c_regression.log::test_i2c_scan: bus recovery took 3 retries

## Suggested Next Checks

- Data mismatch: Compare expected data setup against observed values.
- Environment: Check files, permissions, and license service availability.
