---
name: build
description: 'Implement a feature or change end to end (inspect, plan, build, validate, review). Use for any non-trivial feature, UI work, API work, or multi-file change. Examples: "implement the settings page", "add an endpoint for...", "build this feature", "làm tính năng...", "thêm trang...".'
---

# Build Skill

## 1. Understand
Read the request, `PROJECT.md`, relevant specs (`docs/specs/`, PRD, Figma), and dependency manifests. Find similar implementations. Confirm acceptance criteria and scope.

## 2. Plan
Short plan: files/areas, steps, tests, risks. For Plan-first or multi-step tasks, record the plan in `.agents/tasks/<feature>.md` and wait for approval.

## 3. Implement
Work incrementally. Reuse existing components, services, utilities, and schemas. Do not refactor unrelated code.

Frontend: reuse the design system, use native semantic HTML, keep accessibility, handle loading/empty/error/success/disabled states, check responsive layout, avoid unneeded client state.

Backend: follow existing API conventions, validate input at the boundary, enforce authentication and authorization, return predictable responses, handle expected errors explicitly, keep sensitive data out of logs.

## 4. Validate
Run the format, lint, typecheck, test, and build commands listed in `PROJECT.md`. Use only commands that exist.

## 5. Review
Read your own diff using the `review` skill checklist. Update `CHANGELOG.md`, `TODO.md`, move finished task to `.agents/tasks/archive/`, then deliver the Completion Report.

## Output
The Completion Report from `AGENTS.md`: what was built, key files, checks run with real results, known limits.
