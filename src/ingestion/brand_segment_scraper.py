"""Scrape automobile category pages brand by brand to avoid broad-list limits."""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from src.ingestion.category_page_scraper import BASE_URL as CATEGORY_BASE_URL
from src.ingestion.category_page_scraper import (
    extract_total_count,
    find_browser_executable,
    has_access_challenge,
    has_login_page,
    store_html_page,
)
from src.ingestion.sahibinden_scraper import ScraperConfig, start_browser, wait_for_manual_access_check
from src.ingestion.storage import DEFAULT_DB_PATH

BASE_URL = "https://www.sahibinden.com/otomobil"
CATALOG_PATH = Path("data") / "reference" / "vehicle_catalog.json"
CHECKPOINT_PATH = Path("data") / "runtime" / "brand_segment_checkpoint.json"
SCRAPER_PROFILE_PATH = Path("data") / "runtime" / "edge-profile-category"

SLUG_OVERRIDES = {
    "mercedes - benz": "mercedes-benz",
    "mercedes-benz": "mercedes-benz",
    "ds automobiles": "ds-automobiles",
    "mini": "mini",
    "mg": "mg",
    "rks": "rks",
    "xev": "xev",
    "tofaş": "tofas",
}


@dataclass(frozen=True, slots=True)
class BrandSegment:
    name: str
    slug: str

    @property
    def url_base(self) -> str:
        if self.slug.startswith("http"):
            return self.slug
        return f"{BASE_URL}/{self.slug}"


def slugify_brand(name: str) -> str:
    normalized = name.strip().casefold()
    if normalized in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[normalized]

    ascii_name = (
        unicodedata.normalize("NFKD", normalized)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    ascii_name = ascii_name.replace("&", " ")
    ascii_name = re.sub(r"[^a-z0-9]+", "-", ascii_name)
    return ascii_name.strip("-")


def load_brands(only_brand: str | None = None) -> list[BrandSegment]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    brands = []
    for item in catalog.get("brands", []):
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        if only_brand and name.casefold() != only_brand.casefold():
            continue
        brands.append(BrandSegment(name=name, slug=slugify_brand(name)))
    return brands


def load_checkpoint(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"brand_index": 0, "offset": 0, "completed": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_checkpoint(path: Path, *, brand_index: int, offset: int, completed: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "brand_index": brand_index,
        "offset": offset,
        "completed": completed,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_url(segment: BrandSegment, offset: int, page_size: int) -> str:
    parsed = urlparse(segment.url_base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({"pagingSize": str(page_size), "pagingOffset": str(offset)})
    return urlunparse(parsed._replace(query=urlencode(query)))


def extract_brand_segments_from_html(html: str, catalog_brands: list[BrandSegment]) -> list[BrandSegment]:
    expected = {item.name.casefold(): item.name for item in catalog_brands}
    found: dict[str, BrandSegment] = {}
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.select("a[href]"):
        text = " ".join(link.get_text(" ", strip=True).split())
        text = re.sub(r"\s*\([0-9.\s]+\)\s*$", "", text).strip()
        brand_name = expected.get(text.casefold())
        if not brand_name:
            continue
        href = str(link.get("href", "")).strip()
        if not href or "/ilan/" in href or "pagingOffset" in href:
            continue
        found[brand_name] = BrandSegment(name=brand_name, slug=urljoin(CATEGORY_BASE_URL, href))
    return [found[item.name] for item in catalog_brands if item.name in found]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape Sahibinden automobile category pages brand by brand.")
    parser.add_argument("--brand", default=None, help="Optional single brand, e.g. BMW")
    parser.add_argument("--brands", default=None, help="Comma-separated brand names, e.g. Renault,Volkswagen,BMW")
    parser.add_argument("--brand-limit", type=int, default=None)
    parser.add_argument("--page-size", type=int, default=50, choices=[20, 50])
    parser.add_argument("--pages-per-brand", type=int, default=20, help="Use 0 to keep going until the site ends.")
    parser.add_argument("--delay-min", type=float, default=0.7)
    parser.add_argument("--delay-max", type=float, default=1.5)
    parser.add_argument("--delay-between-brands", type=float, default=5.0)
    parser.add_argument("--manual-wait-seconds", type=float, default=30)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument("--max-empty-pages", type=int, default=1)
    parser.add_argument("--max-low-change-pages", type=int, default=3, help="Use 0 to disable low-change stopping.")
    parser.add_argument("--max-repeated-pages", type=int, default=2, help="Use 0 to disable repeated-page stopping.")
    parser.add_argument("--stop-on-access", action="store_true")
    parser.add_argument("--skip-completed", action="store_true")
    return parser


def filter_brands(brands: list[BrandSegment], brand_filter: str | None, brands_filter: str | None) -> list[BrandSegment]:
    def key(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", slugify_brand(value))

    if brand_filter:
        normalized = key(brand_filter)
        return [brand for brand in brands if key(brand.name) == normalized or key(brand.slug) == normalized]
    if not brands_filter:
        return brands

    requested = {key(item.strip()) for item in brands_filter.split(",") if item.strip()}
    filtered = [
        brand
        for brand in brands
        if key(brand.name) in requested or key(brand.slug) in requested
    ]
    found = {key(brand.name) for brand in filtered} | {key(brand.slug) for brand in filtered}
    missing = sorted(requested - found)
    if missing:
        print(f"Warning: brand filters not matched: {', '.join(missing)}", flush=True)
    return filtered


def page_signature(html: str) -> str:
    return ",".join(re.findall(r'<tr[^>]+data-id="([^"]+)"', html)[:10])


async def run(args: argparse.Namespace) -> None:
    checkpoint_path = Path(args.checkpoint_path)
    if args.reset_checkpoint and checkpoint_path.exists():
        checkpoint_path.unlink()

    checkpoint = load_checkpoint(checkpoint_path)
    completed = [str(item) for item in checkpoint.get("completed", [])]
    catalog_brands = filter_brands(load_brands(None), args.brand, args.brands)
    brands = catalog_brands
    if args.brand_limit is not None:
        brands = brands[: args.brand_limit]
    if not brands:
        raise SystemExit("No brand matched the requested filters.")

    brand_index = int(checkpoint.get("brand_index", 0)) if not (args.brand or args.brands) else 0
    offset = int(checkpoint.get("offset", 0)) if not (args.brand or args.brands) else 0
    config = ScraperConfig(
        query="Otomobil",
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        db_path=args.db_path,
        headless=False,
        browser_executable_path=find_browser_executable(),
        user_data_dir=str(SCRAPER_PROFILE_PATH),
        sandbox=False,
        manual_wait_seconds=args.manual_wait_seconds,
    )
    driver = await start_browser(config)
    try:
        print("Discovering real brand links from otomobil page...", flush=True)
        tab = await driver.get(CATEGORY_BASE_URL)
        await wait_for_manual_access_check(tab, config, "discovering brand links")
        discovered = extract_brand_segments_from_html(await tab.get_content(), catalog_brands)
        if not discovered:
            debug_path = Path("data") / "runtime" / "debug_brand_discovery.html"
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            debug_path.write_text(await tab.get_content(), encoding="utf-8")
            print(
                "Could not discover brand links from the otomobil page. "
                f"Saved debug HTML to {debug_path}. Log in or pass the access check in the opened browser, then retry.",
                flush=True,
            )
            return

        brands_by_name = {item.name: item for item in discovered}
        brands = [brands_by_name[item.name] for item in catalog_brands if item.name in brands_by_name]
        if args.brand_limit is not None:
            brands = brands[: args.brand_limit]
        if args.skip_completed:
            brands = [brand for brand in brands if brand.name not in completed]
            brand_index = 0
            offset = 0
            if not brands:
                print("No pending brand remains after skipping completed entries.", flush=True)
                return
        brands = brands[brand_index:]

        print(
            f"Starting brand segmented scrape. brands_remaining={len(brands)} "
            f"brand_index={brand_index} offset={offset} pages_per_brand={args.pages_per_brand} "
            f"discovered_links={len(discovered)}",
            flush=True,
        )

        for relative_index, segment in enumerate(brands):
            absolute_index = brand_index + relative_index
            current_offset = offset if relative_index == 0 else 0
            empty_pages = 0
            low_change_pages = 0
            repeated_pages = 0
            previous_signature = None
            brand_had_data = False
            max_pages = args.pages_per_brand if args.pages_per_brand > 0 else 1_000_000

            print(f"\nBrand {absolute_index + 1}: {segment.name} ({segment.url_base})", flush=True)
            for page_index in range(1, max_pages + 1):
                url = build_url(segment, current_offset, args.page_size)
                print(f"Opening {url}", flush=True)
                tab = await driver.get(url)
                await wait_for_manual_access_check(tab, config, f"opening {segment.name} offset {current_offset}")
                html = await tab.get_content()
                total_count = extract_total_count(html)
                signature = page_signature(html)

                try:
                    result = store_html_page(html, current_offset, args.page_size, args.db_path)
                except RuntimeError as exc:
                    empty_pages += 1
                    print(f"EMPTY/STOP brand={segment.name} offset={current_offset} error={exc}", flush=True)
                    if has_login_page(html) or has_access_challenge(html):
                        save_checkpoint(
                            checkpoint_path,
                            brand_index=absolute_index,
                            offset=current_offset,
                            completed=completed,
                        )
                        print(f"Access/login page detected for {segment.name}; keeping it pending.", flush=True)
                        if args.stop_on_access:
                            return
                        break
                    if empty_pages >= args.max_empty_pages:
                        break
                else:
                    brand_had_data = True
                    empty_pages = 0
                    if result.changed <= 1:
                        low_change_pages += 1
                    else:
                        low_change_pages = 0
                    next_offset = current_offset + args.page_size
                    save_checkpoint(
                        checkpoint_path,
                        brand_index=absolute_index,
                        offset=next_offset,
                        completed=completed,
                    )
                    print(
                        f"brand={segment.name} page={page_index} offset={result.offset} "
                        f"parsed={result.parsed} changed={result.changed} stored_total={result.stored_total} "
                        f"next_offset={next_offset} total_count={total_count}",
                        flush=True,
                    )
                    current_offset = next_offset

                    if previous_signature and signature and signature == previous_signature:
                        repeated_pages += 1
                        if args.max_repeated_pages > 0 and repeated_pages >= args.max_repeated_pages:
                            print(f"Repeated-page limit reached for {segment.name}; moving on.", flush=True)
                            break
                    else:
                        repeated_pages = 0
                    previous_signature = signature

                    if total_count is not None and current_offset >= total_count:
                        break
                    if args.max_low_change_pages > 0 and low_change_pages >= args.max_low_change_pages:
                        print(f"Low-change page limit reached for {segment.name}; moving on.", flush=True)
                        break

                if page_index < max_pages:
                    time.sleep(random.uniform(args.delay_min, args.delay_max))

            if brand_had_data and segment.name not in completed:
                completed.append(segment.name)
                save_checkpoint(
                    checkpoint_path,
                    brand_index=absolute_index + 1,
                    offset=0,
                    completed=completed,
                )
            else:
                save_checkpoint(
                    checkpoint_path,
                    brand_index=absolute_index,
                    offset=current_offset,
                    completed=completed,
                )
                print(f"Brand {segment.name} did not produce data; keeping it pending.", flush=True)
                break
            if relative_index + 1 < len(brands) and args.delay_between_brands > 0:
                time.sleep(args.delay_between_brands)
    finally:
        driver.stop()


def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
