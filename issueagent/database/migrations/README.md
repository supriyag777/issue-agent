# Database migrations

The SQLAlchemy metadata lives in `backend/app/models/entities.py`. Use Alembic from the repository root after configuring `DATABASE_URL` to generate and apply migrations:

```bash
alembic -c backend/alembic.ini revision --autogenerate -m "initial schema"
alembic -c backend/alembic.ini upgrade head
```

The local Preview startup creates tables for the SQLite demo fallback so the managed preview can boot without a migration service. Docker/PostgreSQL deployments should use committed Alembic revisions as the authoritative schema lifecycle.
