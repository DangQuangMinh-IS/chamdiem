---
trigger: model_decision
description: "Use for database schemas, SQL, ORM models, migrations, indexes, data imports/exports, and any change to stored data."
---

# Data Rules

- Read the current schema and migration history before changing persistence.
- Prefer additive, backward-compatible changes. Use the project's own migration mechanism.
- Consider existing data, nullability and defaults, indexes, uniqueness, foreign keys, query performance, migration ordering, and rollback.
- Destructive schema or data changes (drop, truncate, type narrowing, mass update/delete) need explicit user confirmation and a backup or export first, even for personal projects.
- Never run migrations or scripts against a non-local database without confirmation.
- Never commit real user data or database dumps.
