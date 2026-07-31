from fastapi import APIRouter

from app.api.v1 import health, ingestion, listings

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
