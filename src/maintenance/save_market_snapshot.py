"""Save one real daily market summary for future change calculations."""

from __future__ import annotations

import argparse
from contextlib import closing
from datetime import date

from src.api.database import ListingRepository, SNAPSHOT_TABLE, ensure_snapshot_table


def save_snapshot(repository: ListingRepository, snapshot_date: date) -> int:
    listings = repository.load_listings()
    if listings.empty:
        return 0
    rows: list[tuple[object, ...]] = []
    dimensions = [("market", "all", "market:all", None, listings)]
    for brand, frame in listings.dropna(subset=["brand"]).groupby("brand"):
        if len(frame) >= 8:
            brand_name = str(brand).strip()
            dimensions.append(("brand", brand_name, f"brand:{brand_name.casefold()}", brand_name, frame))
    with closing(repository.connect()) as connection:
        ensure_snapshot_table(connection)
        for dimension_type, dimension_value, dimension_key, brand, frame in dimensions:
            prices = frame["price"]
            rows.append((
                snapshot_date.isoformat(), dimension_type, dimension_value, dimension_key, brand,
                None, None, None,
                float(prices.mean()), float(prices.median()), float(prices.quantile(0.25)),
                float(prices.quantile(0.75)), int(len(frame)),
            ))
        connection.executemany(
            f"""INSERT INTO {SNAPSHOT_TABLE} (
                snapshot_date, dimension_type, dimension_value, dimension_key, brand, series, model, body_type,
                average_price, median_price, q1_price, q3_price, listing_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date, dimension_type, dimension_key)
            DO UPDATE SET average_price=excluded.average_price, median_price=excluded.median_price,
                          q1_price=excluded.q1_price, q3_price=excluded.q3_price, listing_count=excluded.listing_count""",
            rows,
        )
        connection.commit()
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Save real daily market summaries.")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    print(f"saved_snapshots={save_snapshot(ListingRepository(), args.date)}")


if __name__ == "__main__":
    main()
