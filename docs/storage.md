# Optional storage

The application starts with no storage extras or servers. A connection setting activates its client. Install the matching extra first:

| Extra | Enabling setting | Dev Compose profile | Client exposed by dependency |
| --- | --- | --- | --- |
| `postgres-raw` | `APP_POSTGRES_RAW__DSN` | `postgres` | `get_postgres_raw()` → psycopg async pool |
| `postgres-orm` | `APP_POSTGRES_ORM__DSN` | `postgres` | `get_postgres_session()` → SQLAlchemy async session |
| `clickhouse` | `APP_CLICKHOUSE__HOST` | `clickhouse` | `get_clickhouse()` → ClickHouse async client |
| `mongodb` | `APP_MONGODB__DSN` | `mongodb` | `get_mongodb()` → PyMongo async client |
| `redis` | `APP_REDIS__DSN` | `redis` | `get_redis()` → redis.asyncio client |

Each backend also accepts pool and timeout settings such as `APP_POSTGRES_ORM__POOL_SIZE` or `APP_REDIS__SOCKET_TIMEOUT`; see `.env.example` and the configuration page. DSNs and passwords are `SecretStr` values, so they are masked in logs and settings reprs.

For example, run `uv sync --extra postgres-orm` and set `APP_POSTGRES_ORM__DSN=postgresql+psycopg://user:password@host:5432/db`. For local servers, `docker compose -f compose.yml -f compose.dev.yml --profile postgres up -d postgres` starts PostgreSQL with the credentials used in `.env.example`; inside the dev `api` container use the service name (`postgres`, `redis`, `mongodb`, `clickhouse`) as host. Raw psycopg uses `postgresql://...`. The two PostgreSQL extras can coexist with separate DSNs. Client factories live in the infrastructure layer `src/app/infra/storage/`; they initialize during lifespan and close at shutdown. FastAPI dependencies live in `src/app/api/dependencies/storage.py`, so storage modules do not import FastAPI. Endpoints that depend on an unconfigured or unreachable client return a 503 problem response.

To add a backend, define a settings model and optional `Settings` field, a module with `async def create_handle(settings) -> StorageHandle`, a `BackendSpec` entry in `BACKENDS`, a project extra, and a `require(SPEC)` provider. The spec name matches the settings field and readiness metric label.

`/ready` probes every configured backend concurrently with `APP_READINESS_TIMEOUT` (2 seconds by default) and returns 503 while any are unavailable. The result is reused for `APP_READINESS_CACHE_TTL` seconds (5 by default), so frequent probes and scrapes do not load the databases. `/live` remains independent of storage. Client creation does not require an available server at startup. For ClickHouse, configure host, port, credentials, database, and TLS separately through `APP_CLICKHOUSE__*`; its connection is created on the first readiness or dependency check.

## ORM migrations

Install `postgres-orm`, set `APP_POSTGRES_ORM__DSN`, and apply the included initial migration for the optional notes example:

```bash
uv run poe migrate
```

The migration creates `example_notes`. After it runs, `POST /api/v1/notes` accepts `{"content":"hello"}` and `GET /api/v1/notes/{note_id}` reads it. Without `APP_POSTGRES_ORM__DSN`, these routes return 503. For another ORM model, inherit from `app.infra.storage.models.Base`, import it in `migrations/env.py`, then generate a revision with `uv run alembic revision --autogenerate -m 'add model'`. CI runs `alembic check` after migrating. This Alembic setup covers only PostgreSQL ORM models.

The PostgreSQL integration test uses the same `APP_POSTGRES_ORM__DSN`. Start a disposable PostgreSQL database, apply the migration, then run:

```bash
uv run poe test-integration
```

The test creates a note through HTTP and reads it in another request. It is skipped during ordinary local test runs when `APP_POSTGRES_ORM__DSN` is unset. CI starts PostgreSQL, applies the migration, and runs the integration test separately.
