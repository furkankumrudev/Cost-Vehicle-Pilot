"""Scrape Sahibinden automobile listings by city split into transmission filters."""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from src.ingestion.category_page_scraper import (
    DEFAULT_DEBUG_PATH,
    extract_total_count,
    find_browser_executable,
    has_access_challenge,
    has_login_page,
)
from src.ingestion.city_segment_scraper import CITY_NAME_FIXES, CitySegment, load_cities
from src.ingestion.sahibinden_scraper import ScraperConfig, parse_search_results, start_browser, wait_for_manual_access_check
from src.ingestion.storage import DEFAULT_DB_PATH, ListingStore

CHECKPOINT_PATH = Path("data") / "runtime" / "city_transmission_segment_checkpoint.json"
SCRAPER_PROFILE_PATH = Path("data") / "runtime" / "edge-profile-city"

TRANSMISSION_FILTERS = {
    "manuel": ("Manuel", "32467"),
    "manual": ("Manuel", "32467"),
    "duz": ("Manuel", "32467"),
    "otomatik": ("Otomatik", "32466"),
    "automatic": ("Otomatik", "32466"),
}


@dataclass(slots=True)
class PageResult:
    offset: int
    parsed: int
    added: int
    upserted: int
    stored_total: int


@dataclass(frozen=True, slots=True)
class CityTransmissionSegment:
    city: CitySegment
    transmission_name: str
    transmission_value: str

    @property
    def key(self) -> str:
        return f"{self.city.slug}|{self.transmission_name.casefold()}"

    @property
    def city_name(self) -> str:
        return CITY_NAME_FIXES.get(self.city.slug, self.city.name)


def parse_transmissions(value: str | None) -> list[tuple[str, str]]:
    raw_values = value or "manuel,otomatik"
    transmissions: list[tuple[str, str]] = []
    for raw_item in raw_values.split(","):
        item = raw_item.strip().casefold()
        if not item:
            continue
        if item not in TRANSMISSION_FILTERS:
            available = ", ".join(sorted({"manuel", "otomatik"}))
            raise SystemExit(f"Unknown transmission filter: {raw_item}. Available: {available}")
        transmission = TRANSMISSION_FILTERS[item]
        if transmission not in transmissions:
            transmissions.append(transmission)
    if not transmissions:
        raise SystemExit("No valid transmission filters were provided.")
    return transmissions


def load_checkpoint(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"job_index": 0, "offset": 0, "completed": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_checkpoint(path: Path, *, job_index: int, offset: int, completed: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"job_index": job_index, "offset": offset, "completed": completed}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_url(segment: CityTransmissionSegment, offset: int, page_size: int) -> str:
    parsed = urlparse(segment.city.url_base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update(
        {
            "a4": segment.transmission_value,
            "pagingSize": str(page_size),
            "pagingOffset": str(offset),
        }
    )
    return urlunparse(parsed._replace(query=urlencode(query)))


def build_jobs(
    cities: list[CitySegment],
    transmissions: list[tuple[str, str]],
) -> list[CityTransmissionSegment]:
    return [
        CityTransmissionSegment(city=city, transmission_name=name, transmission_value=value)
        for city in cities
        for name, value in transmissions
    ]


def store_transmission_page(
    html: str,
    offset: int,
    page_size: int,
    db_path: str,
    segment: CityTransmissionSegment,
) -> PageResult:
    listings = parse_search_results(html)
    if not listings:
        DEFAULT_DEBUG_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_DEBUG_PATH.write_text(html, encoding="utf-8")
        if has_access_challenge(html):
            raise RuntimeError(f"Access challenge detected. Saved HTML to {DEFAULT_DEBUG_PATH}.")
        raise RuntimeError(f"No listings parsed at offset={offset}. Saved HTML to {DEFAULT_DEBUG_PATH}.")

    for listing in listings:
        if listing.city and listing.city.casefold() != segment.city_name.casefold() and not listing.district:
            listing.district = listing.city
        listing.city = segment.city_name
        listing.transmission = segment.transmission_name

    with ListingStore(db_path) as store:
        previous_total = store.count()
        upserted = store.upsert_many(listings)
        stored_total = store.count()

    return PageResult(
        offset=offset,
        parsed=len(listings),
        added=max(0, stored_total - previous_total),
        upserted=upserted,
        stored_total=stored_total,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape city pages split by transmission filters.")
    parser.add_argument("--city", default=None, help="Optional single city, e.g. ankara")
    parser.add_argument("--city-limit", type=int, default=None)
    parser.add_argument("--start-offset", type=int, default=None)
    parser.add_argument("--transmissions", default=None, help="Comma-separated values: manuel,otomatik")
    parser.add_argument("--page-size", type=int, default=50, choices=[20, 50])
    parser.add_argument("--pages-per-transmission", type=int, default=0, help="Use 0 to keep going until the site ends.")
    parser.add_argument("--delay-min", type=float, default=10.0)
    parser.add_argument("--delay-max", type=float, default=22.0)
    parser.add_argument("--delay-between-transmissions", type=float, default=25.0)
    parser.add_argument("--manual-wait-seconds", type=float, default=180)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument("--max-empty-pages", type=int, default=2)
    parser.add_argument("--max-stale-pages", type=int, default=6, help="Use 0 to disable stale-page stopping.")
    parser.add_argument("--stop-on-access", action="store_true")
    parser.add_argument("--skip-completed", action="store_true")
    return parser


async def run(args: argparse.Namespace) -> None:
    checkpoint_path = Path(args.checkpoint_path)
    if args.reset_checkpoint and checkpoint_path.exists():
        checkpoint_path.unlink()

    cities = load_cities(args.city)
    if not cities:
        available = ", ".join(city.slug for city in load_cities(None))
        raise SystemExit(f"City not found: {args.city}. Available slugs: {available}")
    if args.city_limit is not None:
        cities = cities[: args.city_limit]

    jobs = build_jobs(cities, parse_transmissions(args.transmissions))
    checkpoint = load_checkpoint(checkpoint_path)
    completed = [str(item) for item in checkpoint.get("completed", [])]
    job_index = int(checkpoint.get("job_index", 0))
    offset = args.start_offset if args.start_offset is not None else int(checkpoint.get("offset", 0))

    if args.skip_completed:
        jobs = [job for job in jobs if job.key not in completed and f"{job.key} (empty)" not in completed]
        job_index = 0
        offset = 0
        if not jobs:
            print("No pending city/transmission segment remains after skipping completed entries.", flush=True)
            return

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
        jobs = jobs[job_index:]
        print(
            f"Starting city/transmission segmented scrape. jobs_remaining={len(jobs)} "
            f"job_index={job_index} offset={offset} pages_per_transmission={args.pages_per_transmission}",
            flush=True,
        )

        for relative_index, segment in enumerate(jobs):
            absolute_index = job_index + relative_index
            current_offset = offset if relative_index == 0 else 0
            empty_pages = 0
            stale_pages = 0
            segment_had_data = False
            total_count = None
            max_pages = args.pages_per_transmission if args.pages_per_transmission > 0 else 1_000_000

            print(
                f"\nCity/transmission {absolute_index + 1}: {segment.city_name} "
                f"transmission={segment.transmission_name} ({segment.city.url_base})",
                flush=True,
            )
            for page_index in range(1, max_pages + 1):
                url = build_url(segment, current_offset, args.page_size)
                print(f"Opening {url}", flush=True)
                tab = await driver.get(url)
                await wait_for_manual_access_check(
                    tab,
                    config,
                    f"opening {segment.key} offset {current_offset}",
                )
                html = await tab.get_content()
                if total_count is None:
                    total_count = extract_total_count(html)
                    print(f"reported_total_count={total_count}", flush=True)

                try:
                    result = store_transmission_page(html, current_offset, args.page_size, args.db_path, segment)
                except RuntimeError as exc:
                    print(f"EMPTY/STOP city_transmission={segment.key} offset={current_offset} error={exc}", flush=True)
                    if has_login_page(html) or has_access_challenge(html):
                        save_checkpoint(
                            checkpoint_path,
                            job_index=absolute_index,
                            offset=current_offset,
                            completed=completed,
                        )
                        print(f"Access/login page detected for {segment.key}; keeping it pending.", flush=True)
                        if args.stop_on_access:
                            return
                        break

                    empty_pages += 1
                    if empty_pages >= args.max_empty_pages:
                        print(f"Empty-page limit reached for {segment.key}; moving on.", flush=True)
                        break
                else:
                    segment_had_data = True
                    empty_pages = 0
                    next_offset = current_offset + args.page_size
                    save_checkpoint(
                        checkpoint_path,
                        job_index=absolute_index,
                        offset=next_offset,
                        completed=completed,
                    )
                    print(
                        f"city={segment.city_name} transmission={segment.transmission_name} "
                        f"page={page_index} offset={result.offset} parsed={result.parsed} "
                        f"added={result.added} upserted={result.upserted} stored_total={result.stored_total} "
                        f"next_offset={next_offset} total_count={total_count}",
                        flush=True,
                    )
                    current_offset = next_offset

                    if result.added == 0:
                        stale_pages += 1
                        if args.max_stale_pages > 0 and stale_pages >= args.max_stale_pages:
                            print(
                                f"No new listings for {stale_pages} consecutive pages; moving to next transmission.",
                                flush=True,
                            )
                            break
                    else:
                        stale_pages = 0

                    if total_count is not None and current_offset >= total_count:
                        break

                if page_index < max_pages:
                    time.sleep(random.uniform(args.delay_min, args.delay_max))

            if segment_had_data and segment.key not in completed:
                completed.append(segment.key)
            elif not segment_had_data:
                empty_marker = f"{segment.key} (empty)"
                if empty_marker not in completed:
                    completed.append(empty_marker)
            save_checkpoint(checkpoint_path, job_index=absolute_index + 1, offset=0, completed=completed)

            if relative_index + 1 < len(jobs) and args.delay_between_transmissions > 0:
                time.sleep(args.delay_between_transmissions)
    finally:
        driver.stop()


def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
