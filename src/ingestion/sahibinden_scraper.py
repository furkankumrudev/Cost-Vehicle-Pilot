"""Sahibinden search-result ingestion prototype.

This module collects listing rows from Sahibinden search result pages and writes
normalized records into SQLite. Use it conservatively for bootcamp research and
respect the source site's rules, robots controls, and rate limits.
"""

from __future__ import annotations

import argparse
import asyncio
import random
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from .schema import VehicleListing
from .storage import DEFAULT_DB_PATH, ListingStore

BASE_URL = "https://www.sahibinden.com"


@dataclass(slots=True)
class ScraperConfig:
    query: str
    year_min: str | None = None
    year_max: str | None = None
    engine_volume: str | None = None
    transmission: str | None = None
    max_pages: int = 1
    delay_min: float = 2.5
    delay_max: float = 5.0
    db_path: str = str(DEFAULT_DB_PATH)
    headless: bool = False


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized or None


def parse_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else None


def split_location(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    parts = [part for part in re.split(r"\s*/\s*|\s{2,}", value.strip()) if part]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return parts[0], None


def extract_listing(row: Tag) -> VehicleListing | None:
    source_listing_id = row.get("data-id")

    title_tag = row.select_one("td.searchResultsTitleValue a.classifiedTitle")
    title = clean_text(title_tag.get_text(" ") if title_tag else None)
    if not title:
        return None

    listing_url = None
    if title_tag and title_tag.get("href"):
        listing_url = urljoin(BASE_URL, str(title_tag.get("href")))

    tag_values = [clean_text(tag.get_text(" ")) for tag in row.select("td.searchResultsTagAttributeValue")]
    brand = tag_values[0] if len(tag_values) > 0 else None
    series = tag_values[1] if len(tag_values) > 1 else None
    engine = tag_values[2] if len(tag_values) > 2 else None

    attr_values = [clean_text(tag.get_text(" ")) for tag in row.select("td.searchResultsAttributeValue")]
    year = parse_int(attr_values[0] if len(attr_values) > 0 else None)
    mileage_km = parse_int(attr_values[1] if len(attr_values) > 1 else None)
    color = attr_values[2] if len(attr_values) > 2 else None

    price_tag = row.select_one("td.searchResultsPriceValue div.classified-price-container span")
    price = parse_int(price_tag.get_text(" ") if price_tag else None)

    date_tag = row.select_one("td.searchResultsDateValue")
    listing_date = clean_text(date_tag.get_text(" ") if date_tag else None)

    location_tag = row.select_one("td.searchResultsLocationValue")
    city, district = split_location(clean_text(location_tag.get_text(" ") if location_tag else None))

    image_tag = row.select_one("td.searchResultsLargeThumbnail img")
    image_url = None
    if image_tag:
        image_url = image_tag.get("data-src") or image_tag.get("src")

    return VehicleListing.create(
        source="sahibinden",
        source_listing_id=str(source_listing_id) if source_listing_id else None,
        title=title,
        brand=brand,
        series=series,
        model=None,
        year=year,
        mileage_km=mileage_km,
        transmission=None,
        fuel_type=None,
        body_type=None,
        color=color,
        engine=engine,
        city=city,
        district=district,
        seller_type=None,
        price=price,
        listing_date=listing_date,
        listing_url=listing_url,
        image_url=str(image_url) if image_url else None,
    )


def parse_search_results(html: str) -> list[VehicleListing]:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.searchResultsItem[data-id]")
    listings = []
    for row in rows:
        listing = extract_listing(row)
        if listing:
            listings.append(listing)
    return listings


async def polite_sleep(config: ScraperConfig) -> None:
    await asyncio.sleep(random.uniform(config.delay_min, config.delay_max))


async def click_if_exists(tab: object, selector: str) -> bool:
    element = await tab.select(selector)
    if not element:
        return False
    await element.click()
    return True


async def apply_filters(tab: object, config: ScraperConfig) -> None:
    if config.year_min:
        element = await tab.select('input[name="a5_min"]')
        if element:
            await element.send_keys(config.year_min)
    if config.year_max:
        element = await tab.select('input[name="a5_max"]')
        if element:
            await element.send_keys(config.year_max)

    if config.transmission:
        transmission = config.transmission.lower().strip()
        selector = None
        if transmission in {"manuel", "manual", "duz", "dÃ¼z"}:
            selector = 'a[data-value="32467"].js-attribute.facetedCheckbox'
        elif transmission in {"otomatik", "automatic"}:
            selector = 'a[data-value="32466"].js-attribute.facetedCheckbox'
        if selector:
            await click_if_exists(tab, selector)

    apply_button = await tab.select("button.js-manual-search-button")
    if apply_button:
        await apply_button.click()


async def run_scraper(config: ScraperConfig) -> int:
    import nodriver as uc

    driver = await uc.start(headless=config.headless)
    saved_total = 0
    try:
        tab = await driver.get(BASE_URL)
        await polite_sleep(config)

        try:
            cookie_button = await tab.find("TÃ¼m Ã‡erezleri Kabul Et", best_match=True)
            if cookie_button:
                await cookie_button.click()
                await polite_sleep(config)
        except Exception:
            pass

        search_box = await tab.select("#searchText")
        if not search_box:
            raise RuntimeError("Search input could not be found.")
        await search_box.send_keys(config.query)
        await polite_sleep(config)

        search_button = await tab.select('button[type="submit"][value="Ara"]')
        if not search_button:
            raise RuntimeError("Search button could not be found.")
        await search_button.click()
        await polite_sleep(config)

        suggestion = await tab.select("li.first-child.ui-menu-item a")
        if suggestion:
            await suggestion.click()
            await polite_sleep(config)

        category = await tab.select("#searchCategoryContainer div div ul li:first-child a")
        if category:
            await category.click()
            await polite_sleep(config)

        await click_if_exists(tab, 'a.paging-size.Limit50Passive[title="50"]')
        await apply_filters(tab, config)
        await polite_sleep(config)

        with ListingStore(config.db_path) as store:
            for page_number in range(1, config.max_pages + 1):
                html = await tab.get_content()
                listings = parse_search_results(html)
                saved_total += store.upsert_many(listings)
                print(f"page={page_number} parsed={len(listings)} stored_total={store.count()}")

                if page_number >= config.max_pages:
                    break
                next_button = await tab.select('.prevNextBut[title="Sonraki"]')
                if not next_button:
                    break
                await next_button.click()
                await polite_sleep(config)
    finally:
        driver.stop()
    return saved_total


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect Sahibinden vehicle listing search results.")
    parser.add_argument("--query", required=True, help="Search query, e.g. 'Renault Clio'.")
    parser.add_argument("--year-min", default=None)
    parser.add_argument("--year-max", default=None)
    parser.add_argument("--engine-volume", default=None)
    parser.add_argument("--transmission", default=None, help="manuel or otomatik")
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--delay-min", type=float, default=2.5)
    parser.add_argument("--delay-max", type=float, default=5.0)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--headless", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = ScraperConfig(
        query=args.query,
        year_min=args.year_min,
        year_max=args.year_max,
        engine_volume=args.engine_volume,
        transmission=args.transmission,
        max_pages=args.max_pages,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        db_path=args.db_path,
        headless=args.headless,
    )
    saved_total = asyncio.run(run_scraper(config))
    print(f"Saved or updated listings: {saved_total}")


if __name__ == "__main__":
    main()
