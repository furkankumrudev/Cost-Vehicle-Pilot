"""FastAPI dependency helpers and shared filter definitions."""

from __future__ import annotations

from typing import Annotated

from fastapi import HTTPException, Query

from .database import DatabaseUnavailable, ListingRepository

REPOSITORY = ListingRepository()


def get_repository() -> ListingRepository:
    return REPOSITORY


def safe_repository() -> ListingRepository:
    repository = get_repository()
    try:
        repository.listing_count()
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return repository


class MarketFilters:
    """Filters accepted by market endpoints."""

    def __init__(
        self,
        brand: Annotated[str | None, Query(max_length=80)] = None,
        series: Annotated[str | None, Query(max_length=100)] = None,
        model: Annotated[str | None, Query(max_length=140)] = None,
        body_type: Annotated[str | None, Query(max_length=60)] = None,
        fuel_type: Annotated[str | None, Query(max_length=60)] = None,
        transmission: Annotated[str | None, Query(max_length=60)] = None,
        year_min: Annotated[int | None, Query(ge=1900, le=2100)] = None,
        year_max: Annotated[int | None, Query(ge=1900, le=2100)] = None,
        mileage_max: Annotated[int | None, Query(ge=0, le=2_000_000)] = None,
    ) -> None:
        if year_min is not None and year_max is not None and year_min > year_max:
            raise HTTPException(status_code=422, detail="Minimum yıl maksimum yıldan büyük olamaz.")
        self.brand = brand
        self.series = series
        self.model = model
        self.body_type = body_type
        self.fuel_type = fuel_type
        self.transmission = transmission
        self.year_min = year_min
        self.year_max = year_max
        self.mileage_max = mileage_max

    def as_dict(self) -> dict[str, object]:
        return {
            "brand": self.brand, "series": self.series, "model": self.model,
            "body_type": self.body_type, "fuel_type": self.fuel_type,
            "transmission": self.transmission, "year_min": self.year_min,
            "year_max": self.year_max, "mileage_max": self.mileage_max,
        }
