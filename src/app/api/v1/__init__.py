from fastapi import APIRouter

from app.api.errors import PROBLEM_RESPONSES
from app.api.v1.examples import router as examples_router
from app.api.v1.notes import router as notes_router

router = APIRouter(prefix="/api/v1", responses=PROBLEM_RESPONSES)
router.include_router(examples_router)
router.include_router(notes_router)
