from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.repository import ListingRepository
from app.modules.listings.schemas import (
    FacilityResponse,
    ListingDetailResponse,
    ListingQuoteParams,
    ListingSearchParams,
    ListingSearchResponse,
    ListingSummaryResponse,
    PlatformOfferResponse,
)
from app.modules.pricing.freshness import freshness_status


class ListingService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ListingRepository(session)

    async def search(self, params: ListingSearchParams) -> ListingSearchResponse:
        rows, total = await self.repository.search(params)
        facilities = await self.repository.get_facilities([int(row["id"]) for row in rows])
        items = []
        for row in rows:
            status, age_minutes = freshness_status(row["oldest_price_captured_at"])
            items.append(
                ListingSummaryResponse(
                    **{key: value for key, value in row.items() if key != "id"},
                    facilities=[
                        FacilityResponse(**item) for item in facilities[int(row["id"])]
                    ],
                    freshness_status=status,
                    age_minutes=age_minutes,
                )
            )
        return ListingSearchResponse(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def detail(
        self,
        public_id: str,
        params: ListingQuoteParams,
    ) -> ListingDetailResponse | None:
        listing = await self.repository.get_listing(public_id)
        if listing is None:
            return None
        listing_id = int(listing.pop("id"))
        facilities = await self.repository.get_facilities([listing_id])
        offers = await self.repository.get_offers(listing_id, params)
        enriched_offers = []
        for offer in offers:
            status, age_minutes = freshness_status(offer["captured_at"])
            enriched_offers.append(
                {**offer, "freshness_status": status, "age_minutes": age_minutes}
            )
        return ListingDetailResponse(
            **listing,
            facilities=[FacilityResponse(**item) for item in facilities[listing_id]],
            offers=[PlatformOfferResponse(**offer) for offer in enriched_offers],
        )
