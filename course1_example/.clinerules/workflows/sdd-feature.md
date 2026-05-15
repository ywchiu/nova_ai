# /sdd-feature

When the user asks to add or modify a feature, follow these steps in order. Do not skip steps. Do not parallelize.

1. Clarify requirement. Restate what is being asked and list assumptions. If the user explicitly asked for auto-run / auto-act, continue without waiting for another confirmation; otherwise confirm with the user before continuing.
2. Update spec. Modify the relevant file under specs/. Highlight what changed.
3. Update acceptance criteria. Add or modify entries in specs/acceptance-criteria.md. Each AC must be testable.
4. Write tests first. Add new pytest cases in tests/. Run pytest. Expected: new tests fail. Paste failure output.
5. Implement minimal change. Smallest code change to make new tests pass. No unrelated edits, no opportunistic refactor.
6. Run tests. Run the full pytest suite. Paste output.
7. Summarize. Produce a final report covering:
   - Spec changes
   - New / modified tests
   - Code changes
   - Risks and follow-ups

If the user explicitly asked for auto-run / auto-act, treat normal workflow confirmations as pre-approved and continue through local spec/test/code steps. Still stop before external side effects such as posting an Issue comment, opening a PR, pushing code, deleting data, or changing permissions.
