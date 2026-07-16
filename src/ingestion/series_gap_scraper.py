"""Fill sparse brand/series coverage using discovered Sahibinden filter links."""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import sqlite3
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from src.ingestion import brand_segment_scraper
from src.ingestion.category_page_scraper import (
    BASE_URL as CATEGORY_BASE_URL,
    extract_total_count,
    find_browser_executable,
    has_access_challenge,
    has_login_page,
    store_html_page,
)
from src.ingestion.sahibinden_scraper import ScraperConfig, start_browser, wait_for_manual_access_check
from src.ingestion.storage import DEFAULT_DB_PATH


CATALOG_PATH = Path("data") / "reference" / "vehicle_catalog.json"
CHECKPOINT_PATH = Path("data") / "runtime" / "series_gap_checkpoint.json"
HISTORY_PATH = Path("data") / "runtime" / "series_gap_history.json"
SCRAPER_PROFILE_PATH = Path("data") / "runtime" / "edge-profile-city"


@dataclass(frozen=True, slots=True)
class SeriesTarget:
    brand: str
    series: str
    existing_count: int

    @property
    def identifier(self) -> str:
        return f"{self.brand}\u001f{self.series}"


@dataclass(frozen=True, slots=True)
class SeriesLink:
    target: SeriesTarget
    url_base: str


def option_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", text)


def canonical_series_name(value: object, brand: str) -> str:
    text = str(value or "").strip()
    if option_key(brand) == "mercedesbenz" and len(text) == 1 and text.isalpha():
        return f"{text.upper()} Serisi"
    return text


def find_listing_table(connection: sqlite3.Connection) -> str | None:
    tables = {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    if "vehicle_listings_clean" in tables:
        return "vehicle_listings_clean"
    if "vehicle_listings" in tables:
        return "vehicle_listings"
    return None


def load_series_counts(db_path: str) -> tuple[str, dict[tuple[str, str], int]]:
    path = Path(db_path)
    if not path.exists():
        raise SystemExit(f"Database not found: {path}")

    with sqlite3.connect(path) as connection:
        table_name = find_listing_table(connection)
        if table_name is None:
            raise SystemExit("No vehicle listing table was found in the database.")
        rows = connection.execute(
            f"""
            SELECT brand, series, COUNT(*)
            FROM {table_name}
            WHERE brand IS NOT NULL AND trim(brand) != ''
              AND series IS NOT NULL AND trim(series) != ''
            GROUP BY brand, series
            """
        ).fetchall()

    counts: dict[tuple[str, str], int] = {}
    for brand, series, count in rows:
        key = (option_key(brand), option_key(series))
        if all(key):
            counts[key] = counts.get(key, 0) + int(count)
    return table_name, counts


def catalog_series() -> list[tuple[str, str]]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    entries: list[tuple[str, str]] = []
    for brand_entry in catalog.get("brands", []):
        brand = str(brand_entry.get("name", "")).strip()
        if not brand or "?" in brand:
            continue
        for series_entry in brand_entry.get("series", []):
            series = canonical_series_name(series_entry.get("name", ""), brand)
            if series:
                entries.append((brand, series))
    return entries


def parse_name_filter(value: str | None) -> set[str]:
    return {option_key(item) for item in (value or "").split(",") if option_key(item)}


def select_sparse_targets(
    *,
    db_path: str,
    max_existing_listings: int,
    include_zero: bool,
    brand_filter: str | None,
    series_filter: str | None,
    limit: int | None,
) -> tuple[str, list[SeriesTarget]]:
    table_name, counts = load_series_counts(db_path)
    allowed_brands = parse_name_filter(brand_filter)
    allowed_series = parse_name_filter(series_filter)
    selected: list[SeriesTarget] = []

    for brand, series in catalog_series():
        if allowed_brands and option_key(brand) not in allowed_brands:
            continue
        if allowed_series and option_key(series) not in allowed_series:
            continue
        existing = counts.get((option_key(brand), option_key(series)), 0)
        if existing == 0 and not include_zero:
            continue
        if existing <= max_existing_listings:
            selected.append(SeriesTarget(brand=brand, series=series, existing_count=existing))

    selected.sort(key=lambda item: (item.existing_count, item.brand, item.series))
    return table_name, selected[:limit] if limit else selected


def load_checkpoint(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"target_index": 0, "offset": 0, "completed": [], "unavailable": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_checkpoint(
    path: Path,
    *,
    target_index: int,
    offset: int,
    completed: list[str],
    unavailable: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "target_index": target_index,
                "offset": offset,
                "completed": completed,
                "unavailable": unavailable,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_history(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    targets = payload.get("targets", {})
    if not isinstance(targets, dict):
        return {}
    return {
        str(identifier): dict(record)
        for identifier, record in targets.items()
        if isinstance(record, dict)
    }


def save_history(path: Path, history: dict[str, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"targets": history}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def record_history(
    path: Path,
    history: dict[str, dict[str, object]],
    target: SeriesTarget,
    *,
    status: str,
    parsed: int = 0,
    changed: int = 0,
) -> None:
    history[target.identifier] = {
        "brand": target.brand,
        "series": target.series,
        "existing_count_before": target.existing_count,
        "status": status,
        "parsed": parsed,
        "changed": changed,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    save_history(path, history)


def build_url(url_base: str, offset: int, page_size: int) -> str:
    parsed = urlparse(url_base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({"pagingSize": str(page_size), "pagingOffset": str(offset)})
    return urlunparse(parsed._replace(query=urlencode(query)))


def page_signature(html: str) -> str:
    return ",".join(re.findall(r'<tr[^>]+data-id="([^"]+)"', html)[:10])


def extract_series_links(html: str, targets: list[SeriesTarget]) -> dict[str, SeriesLink]:
    expected = {option_key(target.series): target for target in targets}
    found: dict[str, SeriesLink] = {}
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.select("a[href]"):
        text = " ".join(link.get_text(" ", strip=True).split())
        text = re.sub(r"\s*\([0-9.\s]+\)\s*$", "", text).strip()
        target = expected.get(option_key(text))
        if target is None:
            continue
        href = str(link.get("href", "")).strip()
        if not href or "/ilan/" in href or "pagingOffset" in href:
            continue
        found[target.identifier] = SeriesLink(
            target=target,
            url_base=urljoin(CATEGORY_BASE_URL, href),
        )
    return found


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape sparse Sahibinden brand/series listing groups.")
    parser.add_argument("--brand", default=None, help="Optional brand or comma-separated brands, e.g. Tesla,Kia")
    parser.add_argument("--series", default=None, help="Optional series or comma-separated series, e.g. Model 3,Stinger")
    parser.add_argument("--max-existing-listings", type=int, default=7)
    parser.add_argument("--skip-zero", action="store_true", help="Do not include series with no local listings.")
    parser.add_argument("--series-limit", type=int, default=12, help="Maximum selected series; use 0 for no limit.")
    parser.add_argument("--page-size", type=int, default=50, choices=[20, 50])
    parser.add_argument("--pages-per-series", type=int, default=4, help="Use 0 to keep going until the source ends.")
    parser.add_argument("--delay-min", type=float, default=5.0)
    parser.add_argument("--delay-max", type=float, default=10.0)
    parser.add_argument("--delay-between-series", type=float, default=12.0)
    parser.add_argument("--manual-wait-seconds", type=float, default=180.0)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    parser.add_argument("--history-path", default=str(HISTORY_PATH))
    parser.add_argument(
        "--skip-history",
        action="store_true",
        help="Skip series recorded by a previous completed sparse-series check.",
    )
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-empty-pages", type=int, default=1)
    parser.add_argument("--max-low-change-pages", type=int, default=3)
    parser.add_argument("--max-repeated-pages", type=int, default=1)
    parser.add_argument("--stop-on-access", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


async def run(args: argparse.Namespace) -> None:
    if args.max_existing_listings < 0:
        raise SystemExit("--max-existing-listings must be zero or greater.")

    checkpoint_path = Path(args.checkpoint_path)
    if args.reset_checkpoint and checkpoint_path.exists():
        checkpoint_path.unlink()

    history_path = Path(args.history_path)
    history = load_history(history_path)
    table_name, targets = select_sparse_targets(
        db_path=args.db_path,
        max_existing_listings=args.max_existing_listings,
        include_zero=not args.skip_zero,
        brand_filter=args.brand,
        series_filter=args.series,
        limit=None,
    )
    history_skipped = 0
    if args.skip_history:
        before_history_filter = len(targets)
        targets = [target for target in targets if target.identifier not in history]
        history_skipped = before_history_filter - len(targets)
    if args.series_limit:
        targets = targets[: args.series_limit]
    if not targets:
        message = "No sparse brand/series group matched the requested filters."
        if args.skip_history and history_skipped:
            message = "No unchecked sparse brand/series group remains for the requested filters."
        print(message, flush=True)
        return

    print(
        f"Sparse-series selection from {table_name}: {len(targets)} target(s) "
        f"with at most {args.max_existing_listings} local listings.",
        flush=True,
    )
    if history_skipped:
        print(f"Skipped {history_skipped} target(s) already checked in history.", flush=True)
    for target in targets:
        print(f"  {target.brand} / {target.series}: {target.existing_count}", flush=True)
    if args.dry_run:
        return

    checkpoint = load_checkpoint(checkpoint_path)
    completed = [str(item) for item in checkpoint.get("completed", [])]
    unavailable = [str(item) for item in checkpoint.get("unavailable", [])]
    explicit_selection = bool(args.brand or args.series)
    target_index = int(checkpoint.get("target_index", 0)) if (args.resume or not explicit_selection) else 0
    offset = int(checkpoint.get("offset", 0)) if (args.resume or not explicit_selection) else 0

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
        catalog_brands = brand_segment_scraper.load_brands()
        tab = await driver.get(CATEGORY_BASE_URL)
        await wait_for_manual_access_check(tab, config, "discovering brand links")
        brand_links = {
            item.name: item
            for item in brand_segment_scraper.extract_brand_segments_from_html(
                await tab.get_content(), catalog_brands
            )
        }

        links_by_target: dict[str, SeriesLink] = {}
        targets_by_brand: dict[str, list[SeriesTarget]] = {}
        for target in targets:
            targets_by_brand.setdefault(target.brand, []).append(target)
        for brand, brand_targets in targets_by_brand.items():
            brand_link = brand_links.get(brand)
            if brand_link is None:
                print(f"No current Sahibinden brand link for {brand}; skipping its target series.", flush=True)
                continue
            tab = await driver.get(brand_link.url_base)
            await wait_for_manual_access_check(tab, config, f"discovering {brand} series links")
            links_by_target.update(extract_series_links(await tab.get_content(), brand_targets))

        remaining_targets = targets[target_index:]
        print(
            f"Starting sparse-series scrape. targets_remaining={len(remaining_targets)} "
            f"target_index={target_index} offset={offset} discovered_links={len(links_by_target)}",
            flush=True,
        )

        for relative_index, target in enumerate(remaining_targets):
            absolute_index = target_index + relative_index
            target_id = target.identifier
            if target_id in completed or target_id in unavailable:
                continue
            link = links_by_target.get(target_id)
            if link is None:
                unavailable.append(target_id)
                record_history(
                    history_path,
                    history,
                    target,
                    status="no_current_source_link",
                )
                save_checkpoint(
                    checkpoint_path,
                    target_index=absolute_index + 1,
                    offset=0,
                    completed=completed,
                    unavailable=unavailable,
                )
                print(f"No current series link for {target.brand} / {target.series}; skipped.", flush=True)
                continue

            current_offset = offset if relative_index == 0 else 0
            empty_pages = 0
            low_change_pages = 0
            repeated_pages = 0
            previous_signature = None
            access_blocked = False
            parsed = 0
            changed = 0
            max_pages = args.pages_per_series if args.pages_per_series > 0 else 1_000_000
            print(f"\nSeries {absolute_index + 1}: {target.brand} / {target.series} ({link.url_base})", flush=True)

            for page_index in range(1, max_pages + 1):
                url = build_url(link.url_base, current_offset, args.page_size)
                print(f"Opening {url}", flush=True)
                tab = await driver.get(url)
                await wait_for_manual_access_check(
                    tab, config, f"opening {target.brand} / {target.series} offset {current_offset}"
                )
                html = await tab.get_content()
                total_count = extract_total_count(html)
                signature = page_signature(html)
                try:
                    result = store_html_page(
                        html,
                        current_offset,
                        args.page_size,
                        args.db_path,
                        brand_override=target.brand,
                        series_override=target.series,
                    )
                except RuntimeError as exc:
                    empty_pages += 1
                    print(f"EMPTY/STOP series={target.series} offset={current_offset} error={exc}", flush=True)
                    if has_login_page(html) or has_access_challenge(html):
                        access_blocked = True
                        save_checkpoint(
                            checkpoint_path,
                            target_index=absolute_index,
                            offset=current_offset,
                            completed=completed,
                            unavailable=unavailable,
                        )
                        if args.stop_on_access:
                            return
                        break
                    if empty_pages >= args.max_empty_pages:
                        break
                else:
                    parsed += result.parsed
                    changed += result.changed
                    empty_pages = 0
                    low_change_pages = low_change_pages + 1 if result.changed <= 1 else 0
                    next_offset = current_offset + args.page_size
                    save_checkpoint(
                        checkpoint_path,
                        target_index=absolute_index,
                        offset=next_offset,
                        completed=completed,
                        unavailable=unavailable,
                    )
                    print(
                        f"brand={target.brand} series={target.series} page={page_index} "
                        f"offset={result.offset} parsed={result.parsed} changed={result.changed} "
                        f"stored_total={result.stored_total} next_offset={next_offset} total_count={total_count}",
                        flush=True,
                    )
                    current_offset = next_offset
                    if previous_signature and signature and signature == previous_signature:
                        repeated_pages += 1
                        if args.max_repeated_pages > 0 and repeated_pages >= args.max_repeated_pages:
                            print("Repeated-page limit reached; moving on.", flush=True)
                            break
                    else:
                        repeated_pages = 0
                    previous_signature = signature
                    if total_count is not None and current_offset >= total_count:
                        break
                    if result.parsed < args.page_size:
                        print("Short final page reached; moving on.", flush=True)
                        break
                    if args.max_low_change_pages > 0 and low_change_pages >= args.max_low_change_pages:
                        print("Low-change page limit reached; moving on.", flush=True)
                        break

                if page_index < max_pages:
                    time.sleep(random.uniform(args.delay_min, args.delay_max))

            if access_blocked:
                print(f"Access blocked on {target.brand} / {target.series}; keeping it pending.", flush=True)
                break
            if target_id not in completed:
                completed.append(target_id)
            record_history(
                history_path,
                history,
                target,
                status="scraped" if parsed else "no_listing_page_data",
                parsed=parsed,
                changed=changed,
            )
            save_checkpoint(
                checkpoint_path,
                target_index=absolute_index + 1,
                offset=0,
                completed=completed,
                unavailable=unavailable,
            )
            if relative_index + 1 < len(remaining_targets) and args.delay_between_series > 0:
                time.sleep(args.delay_between_series)
    finally:
        driver.stop()


def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
