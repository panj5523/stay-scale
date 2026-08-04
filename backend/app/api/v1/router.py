from fastapi import APIRouter

from app.api.v1 import (
    ai_conversations,
    auth,
    data_retention,
    health,
    ingestion,
    listings,
    management_review,
    operations,
    platform_sync,
    preference_parsing,
    recommendations,
    review_analysis,
    travel_plans,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
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
api_router.include_router(travel_plans.router, tags=["travel-plans"])
api_router.include_router(review_analysis.router, tags=["review-analysis"])
api_router.include_router(
    management_review.router,
    prefix="/management",
    tags=["management-review"],
)
api_router.include_router(operations.router, prefix="/management", tags=["operations"])
api_router.include_router(data_retention.router, prefix="/management", tags=["data-retention"])
api_router.include_router(platform_sync.router, prefix="/management", tags=["platform-sync"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ai_conversations.router, prefix="/users/ai", tags=["ai-conversations"])
