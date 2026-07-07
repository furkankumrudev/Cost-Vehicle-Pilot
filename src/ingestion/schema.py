"""Shared listing schema for ingestion modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class VehicleListing:
    """Normalized vehicle listing captured from an external source."""

    source: str
    source_listing_id: str | None
    title: str
    brand: str | None
    series: str | None
    model: str | None
    year: int | None
    mileage_km: int | None
    transmission: str | None
    fuel_type: str | None
    body_type: str | None
    color: str | None
    engine: str | None
    city: str | None
    district: str | None
    seller_type: str | None
    price: int | None
    currency: str
    listing_date: str | None
    listing_url: str | None
    image_url: str | None
    scraped_at: str

    @classmethod
    def create(
        cls,
        *,
        source: str,
        title: str,
        source_listing_id: str | None = None,
        brand: str | None = None,
        series: str | None = None,
        model: str | None = None,
        year: int | None = None,
        mileage_km: int | None = None,
        transmission: str | None = None,
        fuel_type: str | None = None,
        body_type: str | None = None,
        color: str | None = None,
        engine: str | None = None,
        city: str | None = None,
        district: str | None = None,
        seller_type: str | None = None,
        price: int | None = None,
        currency: str = "TRY",
        listing_date: str | None = None,
        listing_url: str | None = None,
        image_url: str | None = None,
    ) -> "VehicleListing":
        return cls(
            source=source,
            source_listing_id=source_listing_id,
            title=title,
            brand=brand,
            series=series,
            model=model,
            year=year,
            mileage_km=mileage_km,
            transmission=transmission,
            fuel_type=fuel_type,
            body_type=body_type,
            color=color,
            engine=engine,
            city=city,
            district=district,
            seller_type=seller_type,
            price=price,
            currency=currency,
            listing_date=listing_date,
            listing_url=listing_url,
            image_url=image_url,
            scraped_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
