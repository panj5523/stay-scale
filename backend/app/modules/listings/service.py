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


class ListingService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ListingRepository(session)

    async def search(self, params: ListingSearchParams) -> ListingSearchResponse:
        rows, total = await self.repository.search(params)
        facilities = await self.repository.get_facilities([int(row["id"]) for row in rows])
        items = [
            ListingSummaryResponse(
                **{key: value for key, value in row.items() if key != "id"},
                facilities=[FacilityResponse(**item) for item in facilities[int(row["id"])]],
            )
            for row in rows
        ]
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
        return ListingDetailResponse(
            **listing,
            facilities=[FacilityResponse(**item) for item in facilities[listing_id]],
            offers=[PlatformOfferResponse(**offer) for offer in offers],
        )
