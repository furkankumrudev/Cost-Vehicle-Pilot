"""Public market overview, trend, table and movement routes."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query

from ..database import ListingRepository
from ..dependencies import MarketFilters, safe_repository
from ..schemas import MarketOverview, MarketTableResponse, MoversResponse, TrendResponse
from ..services.market_service import grouped_table, movers, overview
from ..services.trend_service import build_listing_trend

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/overview", response_model=MarketOverview)
def get_overview(filters: MarketFilters = Depends(), repository: ListingRepository = Depends(safe_repository)) -> MarketOverview:
    return MarketOverview(**overview(repository, filters.as_dict()))


@router.get("/trend", response_model=TrendResponse)
def get_trend(
    filters: MarketFilters = Depends(), start_date: date | None = None, end_date: date | None = None,
    repository: ListingRepository = Depends(safe_repository),
) -> TrendResponse:
    if start_date and end_date and start_date > end_date:
        return TrendResponse(available=False, message="Başlangıç tarihi bitiş tarihinden büyük olamaz.")
    points = build_listing_trend(repository.load_listings(filters.as_dict()), start_date, end_date)
    if len(points) < 2:
        return TrendResponse(available=False, message="Bu dönem için yeterli geçmiş veri bulunmuyor.")
    return TrendResponse(available=True, points=points)


@router.get("/table", response_model=MarketTableResponse)
def get_table(
    filters: MarketFilters = Depends(), group_by: str = Query(default="brand", pattern="^(brand|body_type|fuel_type)$"),
    repository: ListingRepository = Depends(safe_repository),
) -> MarketTableResponse:
    rows = grouped_table(repository, filters.as_dict(), group_by)
    return MarketTableResponse(group_by=group_by, rows=rows, message=None if rows else "Seçilen filtreler için tablo verisi yok.")


@router.get("/movers", response_model=MoversResponse)
def get_movers(
    direction: str = Query(default="down", pattern="^(up|down)$"), repository: ListingRepository = Depends(safe_repository),
) -> MoversResponse:
    items = movers(repository, direction)
    return MoversResponse(
        available=bool(items), items=items,
        message=None if items else "Hareket hesaplamak için en az iki gerçek günlük piyasa özeti gerekir.",
    )
