# Infrastructure

- `src/app/infra/storage/` contains optional async clients, readiness checks, and adapters for service ports. It never imports FastAPI, Starlette, or `app.api`.
- Each backend is a `BackendSpec` entry in `BACKENDS` (`base.py`). Its module provides `async def create_handle(settings) -> StorageHandle`, and the spec name matches the `Settings` field and the readiness metric label. `StorageManager` creates configured clients, registers cleanup as each one is created, probes readiness concurrently, and closes everything at shutdown.
- HTTP code gets clients through `require(SPEC)` or `acquire(storage, SPEC)` in `app/api/dependencies/storage.py`.
- To add a backend: a nested settings model and optional `Settings` field, a storage module, a `BackendSpec` in `BACKENDS`, a project extra, and a `require(SPEC)` provider. Import driver modules lazily so the base install works without extras. Update `.env.example`, README, and `docs/storage.md`.
- Adapters implement ports defined in `app/services/`. The notes adapter (`notes.py`) uses the PostgreSQL ORM (`models.py`, `postgres_orm.py`) and the initial migration; see the [migrations guide](../../migrations.md).
- Client creation must not require a reachable server at startup; an outage affects `/ready` only.
- Adapter behavior shared by every implementation belongs in `tests/contracts/`; stub clients with `fake_backends`.
