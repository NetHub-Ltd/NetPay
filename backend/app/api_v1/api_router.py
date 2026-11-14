"""Aggregate all version 1 API routers."""
from fastapi import APIRouter

from app.api_v1.routers.bff_sessions_router import router as bff_sessions_router
from app.api_v1.routers.identity_router import router as identity_router
from app.api_v1.routers.payments_router import router as payments_router

api_router = APIRouter()
api_router.include_router(identity_router)
api_router.include_router(payments_router)
api_router.include_router(bff_sessions_router)
