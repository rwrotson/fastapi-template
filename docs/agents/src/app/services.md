# Services

- `src/app/services/` holds use cases, transport-independent types, errors, and ports (`Protocol` interfaces). It never imports FastAPI, settings, or database drivers; import-linter enforces it.
- Express a port in service terms, beside the use case that needs it, without driver types. The notes example defines `Note`, `NoteRepository`, and `NoteUnitOfWork` in `services/notes.py`.
- Expected failures raise a `ServiceError` subclass (`NotFoundError`, `ConflictError` in `services/errors.py`); define feature-specific subclasses next to the feature (`NoteNotFoundError`). Add a new error kind to the [error handlers](api.md) and to the architecture docs.
- A use case decides which operations form one transaction; the unit of work commits or rolls back. Do not commit inside individual repository methods.
- Test use cases with fakes from `tests/fakes.py`, without FastAPI or a database.
