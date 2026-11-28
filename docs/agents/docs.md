# Docs

- The site is built with ProperDocs from `docs/` and `properdocs.yml`; `docs/agents/` and `docs/plans/` are excluded from it. Check changes with `uv run --all-extras --group docs properdocs build --strict`. See the [toolchain notes](../notes.md#documentation-toolchain).
- `docs/gen_ref_pages.py` generates API pages from source modules. `docs/gen_config_page.py` builds the configuration page from `Settings` field types, defaults, and descriptions, plus the Docker Compose variables.
- Do not edit generated pages (configuration, API reference); edit `Settings` field descriptions and source docstrings instead.
- The generator scripts are type-checked with the rest of the project (mypy strict covers `docs/`).
- Update README, `.env.example`, and the docs pages when changing public settings, endpoints, storage extras, or deployment instructions. Docs pages: `getting_started.md`, `architecture.md`, `storage.md`, `observability.md`, `deployment.md`, `notes.md`.
- Agent guides drift when code moves. Name files and symbols that a reader can check; when you rename or remove a module, setting, or task, search `AGENTS.md` and `docs/agents/` for it and update them in the same change.
