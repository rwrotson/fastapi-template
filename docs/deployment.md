# Docker and VPS deployment

## Local development

```bash
cp .env.example .env
docker compose -f compose.yml -f compose.dev.yml up --build
```

The development stage installs all extras and the dev group, mounts `src/`, and reloads on code changes. It binds to host localhost. Add `--profile postgres`, `--profile redis`, `--profile mongodb`, or `--profile clickhouse` to start local backing services.

## Release and VPS

The release workflow runs for a `v*` tag. It first runs the full CI workflow, then scans the image with Trivy, publishes a production image for `linux/amd64` and `linux/arm64` to `ghcr.io/OWNER/REPO` with the tags `X.Y.Z`, `X.Y`, `latest`, and `sha-…`, and deploys the ProperDocs site to GitHub Pages. Set Pages Source to **GitHub Actions** and permit `v*` tags in the `github-pages` environment. GHCR permissions are granted to the release workflow through `GITHUB_TOKEN`. Set the repository variable `UV_SYNC_EXTRAS` to flags such as `--extra postgres-orm --extra redis` before tagging when the production image needs optional clients. The default image contains only core dependencies. If the image is private, authenticate Docker on the VPS before pulling.

On the VPS, place `compose.yml` and a private `.env` file in one directory. Set `IMAGE_REF` to the exact released image (for example `ghcr.io/OWNER/REPO:0.1.0`), `APP_ENVIRONMENT=production`, `APP_ALLOWED_HOSTS` to your public hostname, and any required service settings. Then:

```bash
docker compose pull
docker compose up -d
docker compose ps
curl http://127.0.0.1:8000/ready
```

The service listens on `127.0.0.1:${APP_PORT:-8000}` of the VPS. Terminate TLS in an external Caddy, Nginx, or Traefik reverse proxy, pass requests to that address, and block `/metrics` publicly. Set HSTS and any request rate limits at the reverse proxy. Allow your Prometheus scraper to reach the internal address. Uvicorn runs with `--proxy-headers`, and Compose sets `FORWARDED_ALLOW_IPS=*` so access logs show the real client address; this is safe only because the port is bound to the host's localhost. Set `FORWARDED_ALLOW_IPS` to your proxy addresses if the port is reachable otherwise. For example, a Caddyfile can deny public metrics while routing API requests:

```caddyfile
api.example.com {
    @metrics path /metrics
    respond @metrics 404
    header Strict-Transport-Security "max-age=31536000"
    reverse_proxy 127.0.0.1:8000
}
```

Set `APP_ALLOWED_HOSTS=["api.example.com"]` for this example. Scrape Prometheus directly from localhost on the VPS. For an ORM deployment, run `docker compose run --rm migrate` with the new image before routing traffic to it. The container runs as a non-root user with a read-only root filesystem and a `/tmp` tmpfs; it writes logs to stdout, and Compose rotates them at 3 × 10 MB. Docker stops the app with a 30-second grace period, and Uvicorn finishes in-flight requests for up to 20 seconds.

`/live` is the container healthcheck; use `/ready` for traffic admission. No automatic SSH deployment occurs. To roll back, set `IMAGE_REF` to an earlier tag and repeat the pull/up commands.
