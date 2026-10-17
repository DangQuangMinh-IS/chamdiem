---
name: architect
description: 'Design or review architecture before substantial work. Use for new applications, new modules, service/API boundaries, data flow, technology choices, or large refactors. Examples: "which stack should I use?", "how should I structure this?", "should I split this into modules?", "thiết kế kiến trúc cho...".'
---

# Architect Skill

## Process

1. Inspect existing architecture docs (`docs/adr/`, `docs/architecture/`), API contracts (`docs/api/`, OpenAPI), schema models, and live code; note patterns worth preserving.
2. Define components and their responsibilities.
3. Describe data flow, persistence, and API boundaries.
4. Identify failure modes, security, and scaling needs (for personal projects: only the scale actually expected).
5. Compare alternatives only when the choice matters; state the trade-off in a few lines.
6. Choose the simplest design that meets current requirements.

## Principles

Clear boundaries, low coupling, high cohesion, boring technology, reversible decisions, incremental evolution.

No queues, microservices, caches, or extra layers without a concrete present need.

Output a short proposal in chat (or record an Architectural Decision Record in `docs/adr/NNNN-<slug>.md` or `docs/architecture/` for major architectural decisions) and wait for approval before building.

## ADR Format (`docs/adr/NNNN-<slug>.md`)

```markdown
# ADR NNNN: [Title]

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Deprecated | Superseded

## Context
[Problem statement, technical constraints, forces, and drivers]

## Decision
[Chosen option and key justification]

## Consequences
- **Positive:** [Benefits]
- **Negative / Risks:** [Trade-offs and mitigations]
```
