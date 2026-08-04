from app.db.base import Base
from app.modules.ai_conversations.models import AIConversation, AIConversationMessage  # noqa: F401
from app.modules.auth.models import AdminUser  # noqa: F401
from app.modules.data_retention.models import ArchiveRestoreRequest  # noqa: F401
from app.modules.ingestion.models import (  # noqa: F401
    IngestionBatch,
    IngestionRecord,
    ListingMatchRecord,
)
from app.modules.listings.models import (  # noqa: F401
    CanonicalListing,
    Facility,
    ListingFacility,
    PlatformListing,
    RoomType,
)
from app.modules.management_review.models import IngestionReviewAudit  # noqa: F401
from app.modules.platform_sync.models import PlatformSyncSource  # noqa: F401
from app.modules.platforms.models import Platform  # noqa: F401
from app.modules.preference_parsing.models import PreferenceParseSession  # noqa: F401
from app.modules.pricing.models import PriceSnapshot  # noqa: F401
from app.modules.recommendations.models import (  # noqa: F401
    RecommendationAdjustment,
    RecommendationResult,
    RecommendationSession,
)
from app.modules.review_analysis.models import (  # noqa: F401
    ListingReview,
    ReviewAnalysisSnapshot,
)
from app.modules.travel_planning.models import TravelPlanDraft  # noqa: F401
from app.modules.users.models import UserAccount, UserFavorite  # noqa: F401

__all__ = ["Base"]
