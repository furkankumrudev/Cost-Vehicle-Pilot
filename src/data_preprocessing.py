"""Data preprocessing pipeline for Cost Vehicle Pilot.

This script standardizes the raw used-car dataset and creates a processed CSV
that can be used by notebooks, model training scripts, and the Streamlit app.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CURRENT_YEAR = 2026

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = ROOT_DIR / "data" / "raw" / "used_car_prices.csv"
PROCESSED_DATA_PATH = ROOT_DIR / "data" / "processed" / "used_car_prices_clean.csv"

COLUMN_MAP = {
    "Brand": "brand",
    "Model": "model",
    "Year": "year",
    "Selling_Price": "price",
    "KM_Driven": "mileage_km",
    "Fuel": "fuel_type",
    "Seller_Type": "seller_type",
    "Transmission": "transmission",
    "Owner": "owner_type",
}


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the raw used-car dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found: {path}")
    return pd.read_csv(path)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename source columns into project-standard column names."""
    missing_columns = sorted(set(COLUMN_MAP) - set(df.columns))
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")
    return df.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich the dataset for modelling and analysis."""
    clean_df = df.copy()

    string_columns = [
        "brand",
        "model",
        "fuel_type",
        "seller_type",
        "transmission",
        "owner_type",
    ]
    for column in string_columns:
        clean_df[column] = clean_df[column].astype(str).str.strip()

    numeric_columns = ["year", "price", "mileage_km"]
    for column in numeric_columns:
        clean_df[column] = pd.to_numeric(clean_df[column], errors="coerce")

    clean_df = clean_df.dropna(subset=numeric_columns + string_columns)
    clean_df = clean_df.drop_duplicates()

    clean_df = clean_df[
        (clean_df["year"].between(1990, CURRENT_YEAR))
        & (clean_df["price"] > 0)
        & (clean_df["mileage_km"] >= 0)
    ]

    price_low, price_high = clean_df["price"].quantile([0.01, 0.99])
    mileage_high = clean_df["mileage_km"].quantile(0.99)
    clean_df = clean_df[
        (clean_df["price"].between(price_low, price_high))
        & (clean_df["mileage_km"] <= mileage_high)
    ]

    clean_df["vehicle_age"] = CURRENT_YEAR - clean_df["year"]
    clean_df["price_currency"] = "INR"

    ordered_columns = [
        "brand",
        "model",
        "year",
        "vehicle_age",
        "mileage_km",
        "fuel_type",
        "seller_type",
        "transmission",
        "owner_type",
        "price",
        "price_currency",
    ]
    return clean_df[ordered_columns].sort_values(["brand", "model", "year"]).reset_index(drop=True)


def save_processed_data(df: pd.DataFrame, path: Path = PROCESSED_DATA_PATH) -> None:
    """Save processed dataset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main() -> None:
    raw_df = load_raw_data()
    standardized_df = standardize_columns(raw_df)
    clean_df = clean_data(standardized_df)
    save_processed_data(clean_df)

    print(f"Raw rows: {len(raw_df)}")
    print(f"Processed rows: {len(clean_df)}")
    print(f"Processed file: {PROCESSED_DATA_PATH}")
    print("Columns:", ", ".join(clean_df.columns))


if __name__ == "__main__":
    main()
