from __future__ import annotations

import sqlite3
import unittest

from src.maintenance.clean_vehicle_data import (
    ModelOutlierPolicy,
    extreme_model_price_outlier_ids,
    standardize_cosmetic_name_variants,
)


class CleanVehicleDataTests(unittest.TestCase):
    def test_extreme_model_price_outlier_requires_a_large_reference_group(self) -> None:
        rows = [
            {"id": index, "brand": "Test", "series": "A", "model": "1.0", "price": 100_000 + (index % 5) * 10_000}
            for index in range(1, 51)
        ]
        rows.append({"id": 51, "brand": "Test", "series": "A", "model": "1.0", "price": 3_000_000})

        self.assertEqual(extreme_model_price_outlier_ids(rows), {51})

    def test_plausible_premium_and_small_groups_are_not_rejected(self) -> None:
        large_group = [
            {"id": index, "brand": "Test", "series": "A", "model": "1.0", "price": 100_000}
            for index in range(1, 51)
        ]
        large_group.append({"id": 51, "brand": "Test", "series": "A", "model": "1.0", "price": 1_000_000})
        small_group = [
            {"id": 100 + index, "brand": "Test", "series": "B", "model": "2.0", "price": 100_000}
            for index in range(48)
        ]
        small_group.append({"id": 200, "brand": "Test", "series": "B", "model": "2.0", "price": 5_000_000})

        self.assertEqual(extreme_model_price_outlier_ids(large_group + small_group), set())

    def test_outlier_policy_keeps_its_thresholds_together(self) -> None:
        policy = ModelOutlierPolicy(min_group_size=10, median_multiplier=12.0, iqr_multiplier=2.0)

        self.assertEqual(policy.min_group_size, 10)
        self.assertEqual(policy.upper_price_bound([100, 100, 100, 100]), 1_200.0)

    def test_cosmetic_name_variants_are_merged_without_touching_plus_packages(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            connection.execute("CREATE TABLE vehicle_listings_clean (series TEXT, model TEXT)")
            connection.executemany(
                "INSERT INTO vehicle_listings_clean (series, model) VALUES (?, ?)",
                [
                    ("i30", "1.6 TDCi Titanium"),
                    ("I30", "1.6 TDCI Titanium"),
                    ("i30", "200 AMG"),
                    ("i30", "200 AMG+"),
                ],
            )

            updated = standardize_cosmetic_name_variants(connection, ["series", "model"])

            self.assertEqual(updated, {"series": 1, "model": 1})
            self.assertEqual(
                connection.execute(
                    "SELECT DISTINCT series FROM vehicle_listings_clean ORDER BY series"
                ).fetchall(),
                [("i30",)],
            )
            models = [
                row[0]
                for row in connection.execute(
                    "SELECT DISTINCT model FROM vehicle_listings_clean ORDER BY model"
                )
            ]
            self.assertEqual(len(models), 3)
            self.assertEqual(sum("tdci titanium" in model.casefold() for model in models), 1)
            self.assertIn("200 AMG", models)
            self.assertIn("200 AMG+", models)


if __name__ == "__main__":
    unittest.main()
