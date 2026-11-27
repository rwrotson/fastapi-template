# Migrations

- `migrations/` is the optional Alembic environment for the `postgres-orm` extra; it covers only PostgreSQL ORM models. `alembic.ini` points to it, and mypy checks it.
- ORM models inherit from `app.infra.storage.models.Base` and are imported in `migrations/env.py`.
- Add an Alembic revision for every ORM schema change: `uv run alembic revision --autogenerate -m '<message>'`, then review it.
- Verify a revision against a migrated PostgreSQL database: `uv run poe migrate`, `uv run alembic check`, then `uv run poe test-integration` with `APP_POSTGRES_ORM__DSN` set. CI runs the same sequence in the `integration` job.
- The initial revision `0001_example_notes.py` belongs to the notes example; see "Remove the examples" in the README.
