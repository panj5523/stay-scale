from fastapi import APIRouter

from app.api.v1 import health, ingestion, listings, preference_parsing, recommendations

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(
    preference_parsing.router,
    prefix="/preference-parses",
    tags=["preference-parsing"],
)
api_router.include_router(
    recommendations.router,
    prefix="/recommendations",
    tags=["recommendations"],
)
