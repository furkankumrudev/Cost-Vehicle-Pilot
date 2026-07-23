"""Pydantic response contracts for the public API."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ApiMessage(BaseModel):
    message: str


class CatalogOption(BaseModel):
    name: str
    listing_count: int | None = None


class CatalogResponse(BaseModel):
    items: list[CatalogOption]


class HealthResponse(BaseModel):
    status: str
    database_available: bool
    table: str | None = None
    listing_count: int | None = None
    message: str | None = None


class MarketOverview(BaseModel):
    median_price: float | None = None
    average_price: float | None = None
    listing_count: int = 0
    last_updated_at: str | None = None
    source_status: str
    change_30d: float | None = None
    change_90d: float | None = None
    change_yoy: float | None = None
    message: str | None = None


class TrendPoint(BaseModel):
    date: date
    median_price: float
    average_price: float
    listing_count: int


class TrendResponse(BaseModel):
    available: bool
    label: str = "İlan tarihine göre medyan fiyat"
    points: list[TrendPoint] = Field(default_factory=list)
    message: str | None = None


class MarketTableRow(BaseModel):
    label: str
    average_price: float
    median_price: float
    listing_count: int
    change_30d: float | None = None
    change_90d: float | None = None
    change_yoy: float | None = None


class MarketTableResponse(BaseModel):
    group_by: str
    rows: list[MarketTableRow]
    message: str | None = None


class MoverItem(BaseModel):
    label: str
    change_percent: float
    average_price: float
    listing_count: int
    direction: str


class MoversResponse(BaseModel):
    available: bool
    items: list[MoverItem] = Field(default_factory=list)
    message: str | None = None


class SimilarListing(BaseModel):
    id: int | None = None
    title: str
    brand: str | None = None
    series: str | None = None
    model: str | None = None
    year: int | None = None
    mileage_km: int | None = None
    price: float
    city: str | None = None
    listing_date: str | None = None
    listing_url: str | None = None
    similarity_score: float | None = None


class ValuationRequest(BaseModel):
    brand: str | None = Field(default=None, max_length=80)
    series: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=140)
    body_type: str | None = Field(default=None, max_length=60)
    fuel_type: str | None = Field(default=None, max_length=60)
    transmission: str | None = Field(default=None, max_length=60)
    year: int | None = Field(default=None, ge=1900, le=2100)
    mileage_km: int | None = Field(default=None, ge=0, le=2_000_000)
    asking_price: int | None = Field(default=None, ge=1)


class ValuationResponse(BaseModel):
    status: str
    estimated_market_value: float | None = None
    recommended_low_price: float | None = None
    recommended_high_price: float | None = None
    median_price: float | None = None
    listing_count: int = 0
    confidence: str | None = None
    price_assessment: str | None = None
    asking_price_delta_percent: float | None = None
    explanation: str
    similar_listings: list[SimilarListing] = Field(default_factory=list)


class SimilarListingsResponse(BaseModel):
    items: list[SimilarListing] = Field(default_factory=list)
    message: str | None = None
