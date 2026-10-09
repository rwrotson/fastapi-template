from dataclasses import dataclass

from fastapi import HTTPException


@dataclass(frozen=True)
class Principal:
    """An authenticated subject supplied by a future auth implementation."""

    subject: str


async def get_current_principal() -> Principal:
    """Fail closed until an application provides an authentication backend."""
    raise HTTPException(status_code=401, detail="Authentication is not configured")
