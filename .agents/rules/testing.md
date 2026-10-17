---
trigger: model_decision
description: "Use when writing or running tests, verifying a change, fixing a failing check, or declaring work complete."
---

# Testing Rules

- Test behavior, not implementation details.
- Consider as relevant: happy path, invalid input, boundaries, failure states, authorization, persistence, loading/empty/error UI states.
- Bug fix: add a regression test that fails before the fix and passes after, when practical.
- Use the repo's existing test framework and conventions.
- Run the narrowest relevant test first, then the broader suite before finishing.
- Never skip, delete, or weaken a test or assertion to get green. If a test is wrong, say why and change it deliberately.
- Never claim a check passed unless it was executed. If it cannot run, say so and why.
