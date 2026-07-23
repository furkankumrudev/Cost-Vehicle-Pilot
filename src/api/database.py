"""Small SQLite repository shared by the API and maintenance commands."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from threading import RLock
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "runtime" / "vehicle_listings.sqlite3"

LISTING_TABLES = ("vehicle_listings_clean", "vehicle_listings")
SNAPSHOT_TABLE = "market_price_snapshots"


class DatabaseUnavailable(RuntimeError):
    """Raised when the local listing database cannot be used."""


class ListingRepository:
    """Parameterized, read-focused access to the local listing database."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._frame_cache: dict[tuple[tuple[str, str], ...], tuple[int, pd.DataFrame]] = {}
        self._cache_lock = RLock()

    def connect(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise DatabaseUnavailable("Veritabanı henüz bulunamadı.")
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def listing_table(self, connection: sqlite3.Connection | None = None) -> str:
        owns_connection = connection is None
        connection = connection or self.connect()
        try:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            tables = {str(row[0]) for row in rows}
            for table in LISTING_TABLES:
                if table in tables:
                    return table
        finally:
            if owns_connection:
                connection.close()
        raise DatabaseUnavailable("İlan tablosu henüz oluşturulmadı.")

    def table_columns(self, table: str) -> set[str]:
        if table not in (*LISTING_TABLES, SNAPSHOT_TABLE):
            raise ValueError("Geçersiz tablo adı.")
        with closing(self.connect()) as connection:
            return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}

    def listing_count(self) -> int:
        with closing(self.connect()) as connection:
            table = self.listing_table(connection)
            return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def load_listings(self, filters: dict[str, Any] | None = None) -> pd.DataFrame:
        """Return real listings only; all user values remain query parameters."""
        filters = filters or {}
        cache_key = tuple(sorted((key, str(value)) for key, value in filters.items() if value is not None and value != ""))
        try:
            mtime = self.db_path.stat().st_mtime_ns
        except FileNotFoundError as exc:
            raise DatabaseUnavailable("Veritabanı henüz bulunamadı.") from exc
        with self._cache_lock:
            cached = self._frame_cache.get(cache_key)
            if cached and cached[0] == mtime:
                return cached[1].copy()

            with closing(self.connect()) as connection:
                table = self.listing_table(connection)
                columns = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}
                selected = [
                    column
                    for column in [
                        "id", "title", "brand", "series", "model", "year", "mileage_km",
                        "transmission", "fuel_type", "body_type", "city", "district", "price",
                        "currency", "listing_date", "listing_url", "image_url", "scraped_at",
                    ]
                    if column in columns
                ]
                if "price" not in selected:
                    raise DatabaseUnavailable("İlan tablosunda fiyat alanı bulunamadı.")

                clauses = ["price IS NOT NULL", "price > 0"]
                params: list[Any] = []
                exact_filters = {
                    "brand": "brand", "series": "series", "model": "model",
                    "body_type": "body_type", "fuel_type": "fuel_type", "transmission": "transmission",
                }
                for key, column in exact_filters.items():
                    value = filters.get(key)
                    if value and column in columns:
                        clauses.append(f"LOWER(COALESCE({column}, '')) = LOWER(?)")
                        params.append(str(value).strip())
                if filters.get("year_min") is not None and "year" in columns:
                    clauses.append("year >= ?")
                    params.append(int(filters["year_min"]))
                if filters.get("year_max") is not None and "year" in columns:
                    clauses.append("year <= ?")
                    params.append(int(filters["year_max"]))
                if filters.get("mileage_max") is not None and "mileage_km" in columns:
                    clauses.append("mileage_km <= ?")
                    params.append(int(filters["mileage_max"]))

                query = f"SELECT {', '.join(selected)} FROM {table} WHERE {' AND '.join(clauses)}"
                frame = pd.read_sql_query(query, connection, params=params)

            for column in ("price", "year", "mileage_km"):
                if column in frame:
                    frame[column] = pd.to_numeric(frame[column], errors="coerce")
            frame = frame.dropna(subset=["price"]).copy()
            self._frame_cache = {key: value for key, value in self._frame_cache.items() if value[0] == mtime}
            self._frame_cache[cache_key] = (mtime, frame)
            return frame.copy()

    def distinct_values(self, column: str, filters: dict[str, Any] | None = None) -> list[str]:
        if column not in {"brand", "series", "model", "body_type", "fuel_type", "transmission"}:
            raise ValueError("Geçersiz filtre alanı.")
        frame = self.load_listings(filters)
        if column not in frame:
            return []
        values = frame[column].dropna().astype(str).str.strip()
        return sorted(value for value in values.unique().tolist() if value)

    def last_updated_at(self) -> str | None:
        with closing(self.connect()) as connection:
            table = self.listing_table(connection)
            columns = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}
            if "scraped_at" not in columns:
                return None
            value = connection.execute(
                f"SELECT MAX(scraped_at) FROM {table} WHERE scraped_at IS NOT NULL"
            ).fetchone()[0]
            return str(value) if value else None


def ensure_snapshot_table(connection: sqlite3.Connection) -> None:
    """Create the forward-looking market snapshot store without backfilling data."""
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SNAPSHOT_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date TEXT NOT NULL,
            dimension_type TEXT NOT NULL,
            dimension_value TEXT NOT NULL,
            dimension_key TEXT NOT NULL,
            brand TEXT,
            series TEXT,
            model TEXT,
            body_type TEXT,
            average_price REAL NOT NULL,
            median_price REAL NOT NULL,
            q1_price REAL,
            q3_price REAL,
            listing_count INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(snapshot_date, dimension_type, dimension_key)
        )
        """
    )
    columns = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({SNAPSHOT_TABLE})")}
    if "dimension_key" not in columns:
        connection.execute(f"ALTER TABLE {SNAPSHOT_TABLE} ADD COLUMN dimension_key TEXT NOT NULL DEFAULT ''")
        connection.execute(
            f"UPDATE {SNAPSHOT_TABLE} SET dimension_key = dimension_type || ':' || LOWER(TRIM(dimension_value)) "
            "WHERE dimension_key = ''"
        )
    connection.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{SNAPSHOT_TABLE}_dimension_date "
        f"ON {SNAPSHOT_TABLE}(dimension_type, dimension_value, snapshot_date)"
    )
    connection.execute(
        f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{SNAPSHOT_TABLE}_identity "
        f"ON {SNAPSHOT_TABLE}(snapshot_date, dimension_type, dimension_key)"
    )
    connection.commit()
