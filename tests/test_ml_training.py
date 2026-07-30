from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from src.ml.predict_price_model import build_feature_frame, estimate_condition_adjustment
from src.ml.train_price_model import TrainingConfig, normalize_text, prepare_training_frame


class TrainingDataTests(unittest.TestCase):
    def test_text_normalization_keeps_missing_values_explicit(self) -> None:
        self.assertEqual(normalize_text(None), "Bilinmiyor")
        self.assertEqual(normalize_text("  Tofaţ  "), "Tofaş")

    def test_training_frame_removes_invalid_rows_and_requires_condition_counts(self) -> None:
        raw = pd.DataFrame({
            "marka": ["Test"] * 10 + ["Test"],
            "seri": ["A"] * 11,
            "model": ["1.0"] * 11,
            "yil": [2020] * 10 + [2020],
            "kilometre": [50_000] * 10 + [90_000_000],
            "vites_tipi": ["Otomatik"] * 11,
            "yakit_tipi": ["Benzin"] * 11,
            "kasa_tipi": ["Sedan"] * 11,
            "renk": ["Beyaz"] * 11,
            "motor_hacmi": [1600] * 11,
            "motor_gucu": [110] * 11,
            "degisen_sayisi": [0] * 11,
            "boyali_sayisi": [0] * 11,
            "kimden": ["Sahibinden"] * 11,
            "fiyat": [800_000] * 10 + [900_000],
        })
        prepared, report = prepare_training_frame(raw, TrainingConfig(max_mileage=750_000))
        self.assertEqual(report.removed_hard_limits, 1)
        self.assertEqual(len(prepared), 10)
        self.assertEqual(prepared["boyali_sayisi"].tolist(), [0] * 10)

    def test_prediction_frame_uses_training_contract(self) -> None:
        frame = build_feature_frame({
            "marka": "Volkswagen", "seri": "Golf", "model": "1.5 TSI",
            "yil": 2021, "kilometre": 55_000, "degisen_sayisi": 0, "boyali_sayisi": 0,
        })
        self.assertEqual(frame.shape, (1, 7))
        self.assertEqual(frame.loc[0, "marka"], "Volkswagen")
        self.assertEqual(frame.loc[0, "degisen_sayisi"], 0)

    def test_condition_adjustment_uses_a_clean_reference_price(self) -> None:
        payload = {
            "marka": "Volkswagen", "seri": "Golf", "model": "1.5 TSI",
            "yil": 2021, "kilometre": 55_000, "degisen_sayisi": 1, "boyali_sayisi": 2,
        }
        with patch("src.ml.predict_price_model.predict_condition_price", side_effect=[1_000_000, 930_000]):
            adjustment = estimate_condition_adjustment(payload)

        self.assertAlmostEqual(adjustment.factor, 0.93)
        self.assertAlmostEqual(adjustment.percent, -7.0)


if __name__ == "__main__":
    unittest.main()
