---
name: debug
description: 'Diagnose and fix bugs, failing tests, build errors, or unexpected behavior by finding the root cause. Use whenever something is broken. Examples: "this throws an error", "the test is failing", "the button does nothing", "sao bị lỗi này", "sửa lỗi...".'
---

# Debug Skill

## Process

1. Reproduce, or precisely understand, the failure. Read the full error and surrounding context.
2. Trace data and control flow.
3. Form 2-3 hypotheses; eliminate them with targeted inspection or tests.
4. Fix the root cause with the smallest change.
5. Add a regression test when practical.
6. Re-run the failing check and related checks.

## Rules

- No random edits until the error disappears.
- Do not suppress exceptions or loosen assertions to hide failures.
- Do not touch unrelated code unless it is part of the root cause.
- Each fix attempt that leaves the same check failing counts toward the 3-attempt Circuit Breaker in `AGENTS.md`. After 3, stop and write the root-cause report.

## Output
Root cause (one or two sentences), the fix and why it works, the regression test added (or why none), and the checks re-run with real results.
