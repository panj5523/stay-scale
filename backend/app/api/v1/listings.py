from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.listings.schemas import (
    ListingDetailResponse,
    ListingQuoteParams,
    ListingSearchParams,
    ListingSearchResponse,
)
from app.modules.listings.service import ListingService

router = APIRouter()


@router.get("", response_model=ListingSearchResponse)
async def search_listings(
    params: Annotated[ListingSearchParams, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ListingSearchResponse:
    return await ListingService(session).search(params)


@router.get("/{public_id}", response_model=ListingDetailResponse)
async def get_listing_detail(
    public_id: str,
    params: Annotated[ListingQuoteParams, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ListingDetailResponse:
    listing = await ListingService(session).detail(public_id, params)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
