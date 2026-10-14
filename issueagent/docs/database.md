# Database design

The production Compose database is PostgreSQL. SQLAlchemy models are kept in `backend/app/models/entities.py` and are created during local startup for the Preview/demo path. Alembic configuration and the migration directory are included for deterministic production migrations.

## Entities

| Entity | Purpose |
|---|---|
| `users` | Hashed application credentials and account identity. |
| `repositories` | User-owned GitHub connection metadata and sealed PAT. |
| `issues` | Provider-synchronized issue snapshot, labels, comments, and metadata. |
| `analyses` | Structured analysis result, bounded code context, provider status, and errors. |
| `code_changes` | Proposed diff, approval state, branch, validation output, commit SHA. |
| `pull_requests` | Draft PR metadata and URL linked one-to-one to a committed change. |

Repository, issue, and analysis queries are scoped through the authenticated user's repository ownership. Tokens are never selected into response schemas.

## Migration safety

Migrations should be additive and run as a finite preparation step before the application is considered ready. Destructive schema changes require a backup/export plan and explicit approval. In Docker, `DATABASE_URL` points to the Postgres service; in Preview demo mode, a local SQLite file keeps the app bootable when a managed runtime provides a MySQL DSN that is not part of the requested stack.
