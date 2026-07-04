# Data

This folder contains the dataset workflow for Cost Vehicle Pilot.

## Current Dataset

The first MVP uses a public used-car price dataset from YBI Foundation:

Source URL: https://raw.githubusercontent.com/ybifoundation/Dataset/main/Car%20Price.csv

The raw dataset contains 4,340 rows and the following columns:

- Brand
- Model
- Year
- Selling_Price
- KM_Driven
- Fuel
- Seller_Type
- Transmission
- Owner

## Folder Structure

```text
data/
  raw/
    used_car_prices.csv
  processed/
    used_car_prices_clean.csv
```

## Important Note

The current dataset is used for the first technical MVP. Prices are in INR, not TRY. The model and dashboard will be designed so the data source can later be replaced with a Turkey-focused dataset or an API-backed data ingestion flow.

## Preprocessing

Run the preprocessing script from the project root:

```bash
python src/data_preprocessing.py
```

The script creates:

```text
data/processed/used_car_prices_clean.csv
```

## Project-Standard Columns

The processed dataset uses these standard columns:

- brand
- model
- year
- vehicle_age
- mileage_km
- fuel_type
- seller_type
- transmission
- owner_type
- price
- price_currency
