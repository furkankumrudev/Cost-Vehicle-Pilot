"""Market and valuation calculations built on real cleaned listings."""

from __future__ import annotations

from contextlib import closing
from typing import Any

import pandas as pd

from src.analysis.market_engine import build_market_analysis

from ..database import ListingRepository
from ..services.trend_service import snapshot_changes, unavailable_changes


def _snapshot_scope(filters: dict[str, Any]) -> tuple[str, str] | None:
    """Use only snapshot dimensions that exactly match the active analysis scope."""
    active = {key: value for key, value in filters.items() if value is not None and value != ""}
    if not active:
        return "market", "all"
    if set(active) == {"brand"}:
        return "brand", str(active["brand"])
    return None


def overview(repository: ListingRepository, filters: dict[str, Any]) -> dict[str, object]:
    listings = repository.load_listings(filters)
    if listings.empty:
        return {
            "median_price": None, "average_price": None, "listing_count": 0,
            "last_updated_at": repository.last_updated_at(), "source_status": "Veri yok",
            "message": "Seçilen filtreler için yeterli ilan bulunamadı.",
        }
    scope = _snapshot_scope(filters)
    with closing(repository.connect()) as connection:
        changes = snapshot_changes(connection, *scope) if scope else unavailable_changes()
    return {
        "median_price": float(listings.price.median()),
        "average_price": float(listings.price.mean()),
        "listing_count": int(len(listings)),
        "last_updated_at": repository.last_updated_at(),
        "source_status": "Temizlenmiş ilan verisi",
        **changes,
    }


def grouped_table(repository: ListingRepository, filters: dict[str, Any], group_by: str) -> list[dict[str, object]]:
    allowed = {"brand": "brand", "body_type": "body_type", "fuel_type": "fuel_type"}
    column = allowed.get(group_by, "brand")
    listings = repository.load_listings(filters)
    if listings.empty or column not in listings:
        return []
    frame = listings.dropna(subset=[column]).copy()
    frame[column] = frame[column].astype(str).str.strip()
    frame = frame[frame[column].ne("")]
    if frame.empty:
        return []
    grouped = frame.groupby(column, as_index=False).agg(
        average_price=("price", "mean"), median_price=("price", "median"), listing_count=("price", "count")
    ).sort_values(["listing_count", "median_price"], ascending=[False, False]).head(100)
    return [
        {
            "label": str(row[0]), "average_price": float(row[1]), "median_price": float(row[2]),
            "listing_count": int(row[3]), "change_30d": None, "change_90d": None, "change_yoy": None,
        }
        for row in grouped.itertuples(index=False, name=None)
    ]


def movers(repository: ListingRepository, direction: str) -> list[dict[str, object]]:
    """Return only true snapshot movement; empty is more honest than guesses."""
    with closing(repository.connect()) as connection:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='market_price_snapshots'"
        ).fetchone()
        if not exists:
            return []
        rows = connection.execute(
            """WITH ranked AS (
                SELECT dimension_value, snapshot_date, median_price, average_price, listing_count,
                       ROW_NUMBER() OVER (PARTITION BY dimension_value ORDER BY snapshot_date DESC) AS rn
                FROM market_price_snapshots WHERE dimension_type='brand'
            )
            SELECT latest.dimension_value, latest.average_price, latest.listing_count,
                   latest.median_price, previous.median_price
            FROM ranked latest JOIN ranked previous ON latest.dimension_value=previous.dimension_value
            WHERE latest.rn=1 AND previous.rn=2"""
        ).fetchall()
    items = []
    for row in rows:
        baseline = float(row[4])
        if not baseline:
            continue
        change = (float(row[3]) - baseline) / baseline * 100
        if (direction == "up" and change > 0) or (direction == "down" and change < 0):
            items.append({
                "label": str(row[0]), "average_price": float(row[1]), "listing_count": int(row[2]),
                "change_percent": change, "direction": "up" if change > 0 else "down",
            })
    return sorted(items, key=lambda item: item["change_percent"], reverse=direction == "up")[:4]


def valuation(repository: ListingRepository, payload: dict[str, Any]) -> dict[str, object]:
    filters = {key: payload.get(key) for key in ("brand", "series", "model", "body_type", "fuel_type", "transmission")}
    listings = repository.load_listings(filters)
    result = build_market_analysis(
        listings, target_year=payload.get("year"), target_mileage=payload.get("mileage_km"),
        selected_model=payload.get("model"), user_price=payload.get("asking_price"),
    )
    if result.get("status") == "empty":
        return {
            "status": "empty", "listing_count": 0,
            "explanation": "Bu araç için yeterli benzer ilan bulunamadı. Filtreleri genişletmeyi deneyin.",
        }
    summary = result["summary"]
    similar = serialize_listings(result["used_listings"])
    return {
        "status": str(result["status"]),
        "estimated_market_value": float(summary["weighted_median"]),
        "recommended_low_price": float(summary["weighted_q1"]),
        "recommended_high_price": float(summary["weighted_q3"]),
        "median_price": float(summary["median"]),
        "listing_count": int(result["count"]), "confidence": str(result["confidence"]),
        "price_assessment": result["market_position"], "asking_price_delta_percent": result["price_delta_pct"],
        "explanation": (
            "Tahmin; aynı araç grubundaki ilanların yıl, kilometre, model yakınlığı ve güncelliğine göre "
            "puanlanması, ardından aykırı fiyatların dışarıda bırakılmasıyla oluşturuldu."
        ),
        "similar_listings": similar,
    }


def serialize_listings(frame: pd.DataFrame, limit: int = 12) -> list[dict[str, object]]:
    fields = ["id", "title", "brand", "series", "model", "year", "mileage_km", "price", "city", "listing_date", "listing_url", "similarity_score"]
    records: list[dict[str, object]] = []
    for item in frame.head(limit).to_dict(orient="records"):
        record = {field: item.get(field) for field in fields}
        for numeric in ("id", "year", "mileage_km"):
            if pd.notna(record.get(numeric)):
                record[numeric] = int(record[numeric])
            else:
                record[numeric] = None
        for numeric in ("price", "similarity_score"):
            if pd.notna(record.get(numeric)):
                record[numeric] = float(record[numeric])
            else:
                record[numeric] = None
        record["title"] = str(record.get("title") or "İlan")
        records.append(record)
    return records
