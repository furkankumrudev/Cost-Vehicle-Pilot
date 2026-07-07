"""SQLite storage adapter for scraped vehicle listings."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .schema import VehicleListing

DEFAULT_DB_PATH = Path("data") / "runtime" / "vehicle_listings.sqlite3"


class ListingStore:
    """Persist normalized vehicle listings in SQLite.

    SQLite is the default local development store. The schema is intentionally
    close to the ML feature set so that PostgreSQL can be added later without
    changing the scraper interface.
    """

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_listing_id TEXT,
                title TEXT NOT NULL,
                brand TEXT,
                series TEXT,
                model TEXT,
                year INTEGER,
                mileage_km INTEGER,
                transmission TEXT,
                fuel_type TEXT,
                body_type TEXT,
                color TEXT,
                engine TEXT,
                city TEXT,
                district TEXT,
                seller_type TEXT,
                price INTEGER,
                currency TEXT NOT NULL DEFAULT 'TRY',
                listing_date TEXT,
                listing_url TEXT,
                image_url TEXT,
                scraped_at TEXT NOT NULL,
                UNIQUE(source, source_listing_id)
            )
            """
        )
        self.connection.commit()

    def upsert_listing(self, listing: VehicleListing) -> bool:
        data = listing.to_dict()
        columns = list(data)
        placeholders = ", ".join([":" + column for column in columns])
        update_columns = [column for column in columns if column not in {"source", "source_listing_id"}]
        update_sql = ", ".join([f"{column}=excluded.{column}" for column in update_columns])

        before = self.connection.total_changes
        self.connection.execute(
            f"""
            INSERT INTO vehicle_listings ({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(source, source_listing_id)
            DO UPDATE SET {update_sql}
            """,
            data,
        )
        self.connection.commit()
        return self.connection.total_changes > before

    def upsert_many(self, listings: Iterable[VehicleListing]) -> int:
        changed = 0
        for listing in listings:
            if self.upsert_listing(listing):
                changed += 1
        return changed

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS total FROM vehicle_listings").fetchone()
        return int(row["total"])

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "ListingStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
