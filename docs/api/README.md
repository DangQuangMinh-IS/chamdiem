# API Contracts & Definitions

This folder holds API specifications, schemas, and contract definitions for the project.

## Conventions
- **REST / HTTP APIs:** Store OpenAPI / Swagger definitions here (e.g. `openapi.yaml` or `swagger.json`).
- **GraphQL / gRPC / tRPC:** Store `.proto` files, `.graphql` schemas, or exported type definitions.
- **Webhook & Third-party Integrations:** Store payload schemas and mock responses.

*Note:* If the project does not expose or consume external APIs (e.g. pure CLI tool, local utility), mark `docs/api/` as `none` in `PROJECT.md` and omit this folder.
