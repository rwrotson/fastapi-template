# Dependencies

- Put runtime imports in `[project].dependencies`, optional backend drivers in the matching extra (`postgres-raw`, `postgres-orm`, `clickhouse`, `mongodb`, `redis`), development tools in the `dev` group, and documentation tools in the `docs` group.
- Change dependencies through uv (`uv add`, `uv remove`) so `pyproject.toml` and `uv.lock` change together. Verify the lock with `uv sync --locked --all-extras --all-groups`.
- Raise a direct dependency's lower bound when code needs a newer API. Verify new or upgraded dependencies against their declared lower bounds and the CI `lowest` job; the locked environment alone does not check them.
- A new storage backend needs its own extra; a configured backend requires its extra, and the base install stays usable without any of them.
- Security floors for transitive dependencies go in `[tool.uv] constraint-dependencies`.
- Use the project environment for tools. Do not install packages manually into `.venv` or treat local installations as declared dependencies.
- `[tool.mypy] files` lists only existing directories (mypy fails on a missing path).
- The uv build backend loads `app` from `src/` (`[tool.uv.build-backend]`, `module-name = "app"`, `module-root = "src"`). `src/app/py.typed` marks the package as typed (PEP 561). See the [build backend notes](../notes.md#build-backend).
- Versioning: `uv run cz bump` bumps the version, updates `CHANGELOG.md`, and tags; `uv run cz changelog` updates the changelog only. See [Commitizen & Versioning](../notes.md#commitizen--versioning).
- `poe audit` exports the locked production dependencies to `requirements-audit.txt` (untracked) and runs pip-audit on it.
