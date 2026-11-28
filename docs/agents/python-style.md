# Python Style

## Code

- Use absolute `app.` imports; Ruff bans relative imports.
- Import a module or package whose name starts with `_` only from modules in the same package and its subpackages.
- MyPy runs with `strict = true` and the Pydantic plugin over `src/`, `tests/`, `migrations/`, and `docs/`. All new code must have complete type annotations. Prefer `X | Y` over `Optional[X]`.
- Frozen models used as default argument values are registered in `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls` in `pyproject.toml`.

## Python Formatting

- Keep function signatures, calls, and collection literals on one line when they fit. When they need wrapping, put one parameter, argument, or item on each line. Add a trailing comma after the last entry when there are two or more entries so Ruff preserves the layout. Do not enable `COM812`.
- Omit optional trailing commas in single-entry forms. Keep the required comma in a single-element tuple and any comma Ruff inserts in a wrapped signature with one parameter.

## Documentation and Comments

- Keep documentation, docstrings, and comments short and factual. Describe each entity's purpose without editorial commentary or tutorials.
- Do not add module docstrings. Package docstrings in `__init__.py` are optional. Put package behavior and important module details in Markdown documentation such as `README.md` or `docs/`.
- Give public classes, functions, and ordinary methods a docstring. Prefer one line describing their overall purpose; do not repeat names, signatures, or type annotations. Ruff checks these in application code. Test functions, fixtures, and standard `dunder` methods are exempt.
- Add docstrings to protected or private objects only when they explain behavior that is not clear from code.
- Keep inline comments only for non-obvious behavior or decisions. Put a short comment on the relevant line when it fits; otherwise place it immediately above. Retain necessary tool directives such as `# noqa` and `# type: ignore`.
- A comment placed above a line or group of lines applies only to it. Separate that line or group from the code before and after it with a blank line, unless it starts or ends a block, so the comment's scope is clear. At module and class level, give each commented constant or attribute its own block, and keep uncommented related definitions together in one block.
- In long functions, methods, and tests, separate logical steps (input validation, setup, execution, result handling; arrange, act, assert) with a single blank line. Do not add comments to label the steps. Keep short functions compact.
- At module level, keep `UPPER_CASE` constants and lowercase objects (loggers, imported modules, routers, apps) in separate blocks divided by a blank line.
- Prefer clearer names and more precise types over comments that restate code.
- Edit `Settings` field descriptions and source docstrings, then rebuild the docs; do not edit generated configuration or API reference pages.
