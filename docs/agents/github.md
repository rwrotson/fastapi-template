# GitHub

- `.github/workflows/ci.yml` triggers on push/PR to `main` and `dev` and is reusable via `workflow_call`. Workflow permissions are `contents: read`; actions are pinned to commit SHAs. Parallel jobs:
    - **`quality`** — `poe fmt-check`, `poe lint`, `poe lint-imports`, `poe typecheck`.
    - **`test`** — `poe test` (95% branch coverage) on Ubuntu.
    - **`lowest`** — installs the lowest allowed direct dependencies with every storage extra (`--resolution lowest-direct`) and runs pytest; it checks the declared lower bounds, which the lock does not.
    - **`integration`** — starts PostgreSQL, applies migrations, runs `alembic check`, then `poe test-live`.
    - **`build`** — `uv build`, `properdocs build --strict`, `poe audit`.
    - **`container`** — builds the `production` image and scans it with Trivy (CRITICAL/HIGH vulnerabilities with an available fix fail the job), then smoke-tests it: runs the image detached on port 8000 and polls `/live` (with `Host: localhost`, an allowed host) for up to 30 seconds; container logs are printed on failure and the container is always removed.
- `.github/workflows/release.yml` triggers on version tags (`v*`) and manual `workflow_dispatch`. It runs CI first, then:
    - **`image`** — on tags, checks that the tag matches `uv version --short`; builds and scans a release candidate with `UV_SYNC_EXTRAS` from the repository variable; on tags only, logs in to GHCR and publishes an amd64/arm64 image to GHCR with `X.Y.Z`, `X.Y`, and `sha-…` tags. Manual runs build and scan the image without logging in or pushing.
    - **`docs`** — version tags only (the `github-pages` environment accepts only `v*` tags); builds the site with `properdocs build --strict` and deploys it to **GitHub Pages** via `actions/upload-pages-artifact` + `actions/deploy-pages` (the `github-pages` environment). The Pages artifact is named `github-pages-<run_attempt>` because reruns keep earlier attempts' artifacts and `deploy-pages` rejects duplicate names.
- Pages Source must be set to **"GitHub Actions"** (Settings → Pages), and the `github-pages` environment must allow the `v*` tag. GHCR access comes from `GITHUB_TOKEN`.
- Dependabot opens weekly PRs for uv dependencies (`uv.lock`), Docker, Docker Compose, GitHub Actions, and pre-commit hooks (`.github/dependabot.yml`).
- `uv run pre-commit install` installs the pre-commit, commit-msg, and pre-push hooks; `uv run pre-commit run --all-files` runs them on all files.
