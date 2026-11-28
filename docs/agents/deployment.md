# Deployment

- The `Dockerfile` has `base`, `builder`, `development`, and `production` stages. The Python base image is pinned by digest and the uv image by version; Dependabot updates both. `UV_SYNC_EXTRAS` (build argument, from the repository variable in releases) selects storage extras for the production image; the default image has only core dependencies.
- The production image runs one Uvicorn worker as a non-root user, logs to stdout, uses `/live` as its healthcheck, applies pending Debian security updates at build time, and removes `pip`. It trusts proxy headers (`--proxy-headers`) from `FORWARDED_ALLOW_IPS`. Prometheus metrics are not multiprocess, so keep one worker.
- `compose.yml` binds the app to `127.0.0.1:${APP_PORT:-8000}`, runs with a read-only root filesystem and a `/tmp` tmpfs, rotates container logs, and has a `migrate` profile service. `FORWARDED_ALLOW_IPS=*` is safe only while the port stays bound to localhost; set proxy addresses otherwise.
- `compose.dev.yml` adds the hot-reload `development` stage and the optional `postgres`, `redis`, `mongodb`, and `clickhouse` profiles.
- An external reverse proxy terminates TLS and must block public access to `/metrics`. Set HSTS and rate limits there.
- Releases publish images from `v*` tags only; manual `workflow_dispatch` runs build and scan without pushing. The VPS update is manual: set `IMAGE_REF` to the released tag, run `docker compose pull && docker compose up -d`; for an ORM deployment, run `docker compose run --rm migrate` first. Roll back by setting an earlier `IMAGE_REF`.
- Lint Dockerfiles with hadolint (pre-commit hook). Verify image changes with `docker build --target production .`.
- Update `docs/deployment.md`, README, and `.env.example` when changing deployment instructions or variables.
