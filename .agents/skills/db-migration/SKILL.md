---
name: db-migration
description: 'Design and apply database schema or data changes safely. Use for new tables/columns, index changes, migrations, backfills, or any change to stored data. Examples: "add a column to...", "create a new table for...", "migrate the data", "thêm bảng...", "đổi cấu trúc database".'
---

# DB Migration Skill

## Process

1. Read the existing schema definition (`prisma/schema.prisma`, `db/schema.sql`, ORM entity models) and migration history (`migrations/`).
2. Find existing query/data-access patterns.
3. Define the minimal schema change; prefer additive and backward compatible.
4. Check existing data, nullability/defaults, constraints, and rollback path.
5. Add indexes only when a real query pattern justifies them.
6. Create the migration with the project's own tooling.
7. Validate the generated SQL and run it against a local database only.
8. Test the important read/write paths.

## Safety

For destructive operations (drop, truncate, narrowing a type, mass update/delete): stop, explain the impact, recommend a backup/export, and wait for explicit confirmation.
