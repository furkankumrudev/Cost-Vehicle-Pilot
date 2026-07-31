from __future__ import annotations

import unittest

from src.maintenance.clean_vehicle_data import ModelOutlierPolicy, extreme_model_price_outlier_ids


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


if __name__ == "__main__":
    unittest.main()
