## Development Philosophy

This project follows Spec-Driven Development and Test-Driven Development.

Before implementing or changing behavior:

1. Update or confirm the relevant spec under specs/.
2. Define or update acceptance criteria.
3. Add or update tests that reflect the acceptance criteria.
4. Implement the minimal code needed to pass the tests.
5. Run the relevant tests and report results.

If a request bypasses this flow, ask before proceeding.

## Safety Rules

- Do not modify or delete files under sample_logs/.
- All generated reports must be written under output/.
- Do not overwrite existing reports unless explicitly requested.
- Do not introduce external dependencies unless necessary and explained.
- Do not read secrets, license keys, or production config.

## Coding Rules

- Use Python standard library first.
- Keep functions small and testable.
- Prefer pure functions for parsing and classification.
- Separate parsing, classification, aggregation, and report generation into distinct modules.
- Use pathlib.Path instead of os.path.
- Use logging instead of print.
- Type hints on all public functions.

## Testing Rules

- Every behavior change must include a corresponding test.
- Tests should map back to a specific acceptance criterion.
- Do not weaken tests just to make them pass.
- If a test fails, explain whether the issue is in the implementation, the test, or the spec.
- Debug fixes must include a regression test.
- Use tmp_path for any test that touches the filesystem.

## Output Rules

Markdown report must include:

- Overview
- Failure Groups
- Warnings, only if warnings exist
- Repeated Error Signatures, only if repeated signatures exist
- Suggested Next Checks

CSV report must include columns:

`file, test_name, error_category, error_message, line_number`

Do not rename these existing columns when adding new features. If WARNING support is added, append `warning_message`. If repeated signatures need CSV output later, add new columns only after the existing required columns.

## Task Index

When the task involves analyzing logs, use the `log-error-analysis` skill from `.cline/skills/log-error-analysis/SKILL.md` before parsing or summarizing logs.

When asked to develop or modify a feature, follow the workflow in `.clinerules/workflows/sdd-feature.md`.

When asked to summarize logs, follow the workflow in `.clinerules/workflows/summarize-logs.md`.
