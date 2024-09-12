from fastapi import APIRouter
from .token_routes import router as token_router

router = APIRouter()

router.include_router(token_router, prefix="/api", tags=["tokens"])

