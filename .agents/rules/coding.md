---
trigger: model_decision
description: "Use when writing, changing, refactoring, or reviewing code in any language."
---

# Coding Rules

- Inspect before editing. Search the repo for an existing pattern before adding a helper, component, hook, or abstraction.
- Make the smallest change that fully solves the problem. No unrelated refactors, dependency upgrades, library swaps, or drive-by fixes; mention them in the report instead.
- Preserve existing naming, folder structure, error handling, state management, data access, and test conventions.
- Prefer simple, readable code over clever code. Use strong types, small focused functions, and explicit error handling.
- Avoid `any`, magic numbers, and speculative abstractions. Abstract only after a pattern repeats three times.
- Never suppress compiler/linter errors or swallow exceptions without understanding the cause. If suppression is justified, comment why.
- Leave no dead code, commented-out blocks, or debug logging behind.
- Before adding a dependency, check whether existing dependencies or the standard library cover it.
- Bug fix: reproduce or precisely understand the failure first, then fix the root cause.
