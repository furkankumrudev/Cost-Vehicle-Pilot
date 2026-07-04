# Data Dictionary

## Raw Dataset

Source file: `data/raw/used_car_prices.csv`

| Column | Description |
| --- | --- |
| Brand | Vehicle brand |
| Model | Vehicle model / listing name |
| Year | Manufacturing year |
| Selling_Price | Listed or selling price |
| KM_Driven | Vehicle mileage in kilometers |
| Fuel | Fuel type |
| Seller_Type | Seller category |
| Transmission | Gearbox type |
| Owner | Ownership history |

## Processed Dataset

Source file: `data/processed/used_car_prices_clean.csv`

| Column | Description |
| --- | --- |
| brand | Standardized vehicle brand |
| model | Standardized model/listing name |
| year | Manufacturing year |
| vehicle_age | Vehicle age calculated as 2026 - year |
| mileage_km | Mileage in kilometers |
| fuel_type | Fuel type |
| seller_type | Seller category |
| transmission | Gearbox type |
| owner_type | Ownership history |
| price | Target variable for price prediction |
| price_currency | Currency of the current dataset |

## Current Data Quality Snapshot

After preprocessing:

- Raw rows: 4,340
- Processed rows: 3,470
- Missing values in required fields: 0
- Current currency: INR
- Outlier handling: 1st-99th percentile filtering for price and 99th percentile filtering for mileage
