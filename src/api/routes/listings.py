"""Comparable listing route for secondary UI views."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..database import ListingRepository
from ..dependencies import MarketFilters, safe_repository
from ..schemas import SimilarListingsResponse
from ..services.market_service import serialize_listings

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.get("/similar", response_model=SimilarListingsResponse)
def similar_listings(filters: MarketFilters = Depends(), repository: ListingRepository = Depends(safe_repository)) -> SimilarListingsResponse:
    items = serialize_listings(repository.load_listings(filters.as_dict()).sort_values("scraped_at", ascending=False))
    return SimilarListingsResponse(items=items, message=None if items else "Benzer ilan bulunamadı.")
