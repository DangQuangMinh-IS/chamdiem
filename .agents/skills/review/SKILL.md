---
name: review
description: 'Review a diff or finished work for correctness, security, regressions, and missing tests, and verify acceptance criteria. Use before declaring work done, before merging, or when asked to review or QA. Examples: "review my changes", "is this safe to merge?", "check this before I commit", "kiểm tra lại giúp tôi".'
---

# Review Skill

## Order

1. Correctness against requirements and acceptance criteria
2. Security
3. Data integrity
4. Error handling and edge/boundary cases
5. Regression risk
6. Performance
7. Maintainability and unnecessary complexity
8. Tests (do they cover behavior, failures, permissions?)
9. Scope: unrelated edits, secrets, debug leftovers

## Behavior

Read the diff and the surrounding code, then run the existing automated checks.

For each finding give: problem, impact, recommended fix. Skip formatting nits already enforced by tooling.

Bug fixes: state what failed, why, what changed, why it fixes the root cause, and which test prevents recurrence. Compiling is not proof of a fix.

If there are no meaningful findings, say so and list what was validated.
