# Scraper Strategy

## Goal

ArabamFiyat.com should not depend only on a static dataset. The product architecture includes a data ingestion layer that can collect recent vehicle listing data, store it in a database, and feed the ML pipeline.

## Current Decision

The first ingestion prototype targets Sahibinden search result pages and stores normalized listing rows in SQLite.

Default local database:

```text
data/runtime/vehicle_listings.sqlite3
```

SQLite is used for local development because it is easy to run during the bootcamp. PostgreSQL can be added later by keeping the same normalized listing schema.

## Responsible Use

Scraping can be fragile and may be restricted by website terms, robots controls, or anti-bot protections. For this bootcamp project, the scraper should be used conservatively for learning and prototyping. The final product narrative should describe the ingestion layer as a module that can work with approved data sources, partner feeds, or official APIs.

## MVP Flow

```text
Sahibinden search results
  -> scraper
  -> SQLite listing database
  -> preprocessing pipeline
  -> model training dataset
  -> regression model
  -> prediction API / dashboard
```

## Daily Commands

Genel son 24 saat ilanları:

```bat
scripts\run_daily_update.bat
```

Boyasız/değişensiz filtreli temiz iddialı son 24 saat ilanları:

```bat
scripts\run_daily_clean_update.bat
```

Her iki komut da fiyat bantlarına bölerek tarama yapar. Ortak scraper modülü `src/ingestion/recent_listing_scraper.py` dosyasıdır.

## Current Captured Fields

The search-result prototype captures the fields that are visible on listing result rows:

- source
- source_listing_id
- title
- brand
- series
- year
- mileage_km
- color
- engine
- city
- district
- price
- listing_date
- listing_url
- image_url
- paint_status
- changed_part_status
- damage_status
- is_clean_claimed
- scrape_segment
- scraped_at

## Next Improvements

Some important fields may require visiting each listing detail page:

- fuel_type
- transmission
- body_type
- seller_type
- replaced_parts_count
- painted_parts_count
- engine_power_hp

These fields should be added in a second ingestion step only after the search-result pipeline is stable.

## Bootcamp Value

This architecture shows that ArabamFiyat.com is designed as a sustainable product:

- New listings can be collected over time.
- The model can be retrained when enough new data is available.
- Prediction outputs can stay closer to market changes.
- The data source can be replaced without rewriting the ML and app layers.

## Browser Path

If Chrome is not installed or cannot be auto-detected, pass a browser executable explicitly:

```bash
python -m src.ingestion.sahibinden_scraper --query "Renault Clio" --max-pages 1 --browser-executable-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```
## Current Notes

The local scraper uses a persistent Edge profile under `data/runtime/` so that manual login/access checks can be completed when required. Runtime files, SQLite databases, checkpoints, browser profiles, and debug HTML are local-only and are not committed to Git.
