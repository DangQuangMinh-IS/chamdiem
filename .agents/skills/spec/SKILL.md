---
name: spec
description: 'Turn a vague idea or feature request into a short implementation-ready spec (goal, flow, acceptance criteria, non-goals). Use for new features, MVP scoping, user stories, or when requirements are unclear. Examples: "I want an app that...", "add a feature for...", "what should the first version include?", "tôi muốn làm tính năng...".'
---

# Spec Skill

## Process

1. Check existing internal docs (`docs/specs/`, `docs/features/`, `docs/api/`) and code; ingest external sources if provided (Notion/Confluence PRD, Figma/Miro flows, Jira/Linear stories). Infer from existing product before asking questions.
2. State the user problem, target user, and desired outcome.
3. Describe the primary user flow.
4. List functional requirements.
5. List edge, empty, error, loading, and permission states.
6. Write testable acceptance criteria.
7. Mark non-goals explicitly. Keep the first version as small as possible.

## Output

Goal, User, Flow, Requirements, Acceptance criteria, Edge cases, Non-goals. For substantive features, save the spec to `docs/specs/<feature>.md` or an execution plan in `.agents/tasks/<feature>.md`. Add Open questions only if they block implementation.

Do not invent features without evidence. A feature is not done if the happy path works but other states are broken.
