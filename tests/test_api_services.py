from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date
from pathlib import Path

import pandas as pd

from src.api.database import DatabaseUnavailable, ListingRepository
from src.api.dependencies import MarketFilters
from src.api.routes.market import get_movers, get_overview, get_trend
from src.api.routes.valuation import create_valuation
from src.api.schemas import ValuationRequest
from src.api.services.market_service import _snapshot_scope, build_price_relationships
from src.api.services.trend_service import build_listing_trend
from src.maintenance.save_market_snapshot import save_snapshot


class ApiServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "listings.sqlite3"
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """CREATE TABLE vehicle_listings_clean (
                    id INTEGER PRIMARY KEY, title TEXT, brand TEXT, series TEXT, model TEXT,
                    year INTEGER, mileage_km INTEGER, transmission TEXT, fuel_type TEXT,
                    body_type TEXT, city TEXT, price INTEGER, currency TEXT,
                    listing_date TEXT, listing_url TEXT, image_url TEXT, scraped_at TEXT
                )"""
            )
            connection.executemany(
                """INSERT INTO vehicle_listings_clean VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (1, "Test Sedan", "Test", "A", "1.0", 2020, 80000, "Otomatik", "Benzin", "Sedan", "Ankara", 900000, "TRY", "1 Temmuz 2026", "https://example.test/1", None, "2026-07-01T12:00:00"),
                    (2, "Test Sedan", "Test", "A", "1.0", 2021, 65000, "Otomatik", "Benzin", "Sedan", "Ankara", 1000000, "TRY", "2 Temmuz 2026", "https://example.test/2", None, "2026-07-02T12:00:00"),
                ],
            )
            connection.commit()
        self.repository = ListingRepository(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_trend_uses_real_listing_dates(self) -> None:
        frame = pd.DataFrame({"listing_date": ["1 Temmuz 2026", "2 Temmuz 2026"], "price": [900000, 1000000]})
        trend = build_listing_trend(frame)
        self.assertEqual(len(trend), 2)
        self.assertEqual(trend[0]["median_price"], 900000.0)

    def test_overview_and_empty_history_are_honest(self) -> None:
        overview = get_overview(MarketFilters(), self.repository)
        self.assertEqual(overview.listing_count, 2)
        self.assertIsNone(overview.change_30d)

        trend = get_trend(MarketFilters(), None, None, self.repository)
        self.assertTrue(trend.available)

        movers = get_movers("down", self.repository)
        self.assertFalse(movers.available)

    def test_valuation_returns_low_sample_not_fake_price(self) -> None:
        response = create_valuation(
            ValuationRequest(brand="Test", series="A", model="1.0", year=2020, mileage_km=80000),
            self.repository,
        )
        self.assertEqual(response.status, "low_sample")
        self.assertEqual(response.listing_count, 2)

    def test_missing_database_is_reported(self) -> None:
        missing = ListingRepository(Path(self.temp_dir.name) / "missing.sqlite3")
        with self.assertRaises(DatabaseUnavailable):
            missing.listing_count()

    def test_repository_falls_back_to_raw_table_when_clean_table_is_empty(self) -> None:
        with closing(self.repository.connect()) as connection:
            connection.execute("DELETE FROM vehicle_listings_clean")
            connection.execute(
                """CREATE TABLE vehicle_listings (
                    id INTEGER PRIMARY KEY, title TEXT, brand TEXT, series TEXT, model TEXT,
                    year INTEGER, mileage_km INTEGER, price INTEGER
                )"""
            )
            connection.execute(
                """INSERT INTO vehicle_listings
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (1, "Ham ilan", "Test", "A", "1.0", 2020, 80_000, 900_000),
            )
            connection.commit()

        self.assertEqual(self.repository.listing_table(), "vehicle_listings")
        self.assertEqual(self.repository.listing_count(), 1)

    def test_snapshot_save_is_idempotent_for_one_day(self) -> None:
        snapshot_date = date(2026, 7, 23)
        self.assertEqual(save_snapshot(self.repository, snapshot_date), 1)
        self.assertEqual(save_snapshot(self.repository, snapshot_date), 1)
        with closing(self.repository.connect()) as connection:
            count = connection.execute("SELECT COUNT(*) FROM market_price_snapshots").fetchone()[0]
        self.assertEqual(count, 1)

    def test_snapshot_scope_never_uses_market_change_for_a_narrow_filter(self) -> None:
        self.assertEqual(_snapshot_scope({}), ("market", "all"))
        self.assertEqual(_snapshot_scope({"brand": "Test"}), ("brand", "Test"))
        self.assertIsNone(_snapshot_scope({"brand": "Test", "year_min": 2020}))


    def test_price_relationships_use_real_years_and_mileage_bands(self) -> None:
        frame = pd.DataFrame({
            "year": [2020, 2020, 2020, 2021, 2021, 2021],
            "mileage_km": [20_000, 25_000, 22_000, 80_000, 90_000, 95_000],
            "price": [900_000, 920_000, 910_000, 1_000_000, 1_020_000, 980_000],
        })
        result = build_price_relationships(frame)
        self.assertEqual([point["label"] for point in result["year_points"]], ["2020", "2021"])
        self.assertEqual(result["mileage_points"][0]["label"], "0-25 bin km")
        self.assertEqual(result["mileage_points"][0]["listing_count"], 3)


if __name__ == "__main__":
    unittest.main()
