"""Scrape Sahibinden automobile listings by district for dense cities."""

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
    BASE_URL,
    extract_total_count,
    find_browser_executable,
    has_access_challenge,
    has_login_page,
    store_html_page,
)
from src.ingestion.sahibinden_scraper import ScraperConfig, start_browser, wait_for_manual_access_check
from src.ingestion.storage import DEFAULT_DB_PATH

CHECKPOINT_PATH = Path("data") / "runtime" / "district_segment_checkpoint.json"
SCRAPER_PROFILE_PATH = Path("data") / "runtime" / "edge-profile-city"


@dataclass(frozen=True, slots=True)
class DistrictSegment:
    city_name: str
    city_slug: str
    district_name: str
    district_slug: str

    @property
    def url_base(self) -> str:
        return f"{BASE_URL}/{self.city_slug}-{self.district_slug}"

    @property
    def key(self) -> str:
        return f"{self.city_slug}/{self.district_slug}"


RAW_DISTRICTS = {
    "adana": (
        "Adana",
        [
            ("Aladag", "aladag"),
            ("Ceyhan", "ceyhan"),
            ("Cukurova", "cukurova"),
            ("Feke", "feke"),
            ("Imamoglu", "imamoglu"),
            ("Karaisali", "karaisali"),
            ("Karatas", "karatas"),
            ("Kozan", "kozan"),
            ("Pozanti", "pozanti"),
            ("Saimbeyli", "saimbeyli"),
            ("Saricam", "saricam"),
            ("Seyhan", "seyhan"),
            ("Tufanbeyli", "tufanbeyli"),
            ("Yumurtalik", "yumurtalik"),
            ("Yuregir", "yuregir"),
        ],
    ),
    "antalya": (
        "Antalya",
        [
            ("Akseki", "akseki"),
            ("Aksu", "aksu"),
            ("Alanya", "alanya"),
            ("Demre", "demre"),
            ("Dosemealti", "dosemealti"),
            ("Elmali", "elmali"),
            ("Finike", "finike"),
            ("Gazipasa", "gazipasa"),
            ("Gundogmus", "gundogmus"),
            ("Ibradi", "ibradi"),
            ("Kas", "kas"),
            ("Kemer", "kemer"),
            ("Kepez", "kepez"),
            ("Konyaalti", "konyaalti"),
            ("Korkuteli", "korkuteli"),
            ("Kumluca", "kumluca"),
            ("Manavgat", "manavgat"),
            ("Muratpasa", "muratpasa"),
            ("Serik", "serik"),
        ],
    ),
    "istanbul": (
        "\u0130stanbul",
        [
            ("Adalar", "adalar"),
            ("Arnavutkoy", "arnavutkoy"),
            ("Atasehir", "atasehir"),
            ("Avcilar", "avcilar"),
            ("Bagcilar", "bagcilar"),
            ("Bahcelievler", "bahcelievler"),
            ("Bakirkoy", "bakirkoy"),
            ("Basaksehir", "basaksehir"),
            ("Bayrampasa", "bayrampasa"),
            ("Besiktas", "besiktas"),
            ("Beykoz", "beykoz"),
            ("Beylikduzu", "beylikduzu"),
            ("Beyoglu", "beyoglu"),
            ("Buyukcekmece", "buyukcekmece"),
            ("Catalca", "catalca"),
            ("Cekmekoy", "cekmekoy"),
            ("Esenler", "esenler"),
            ("Esenyurt", "esenyurt"),
            ("Eyupsultan", "eyupsultan"),
            ("Fatih", "fatih"),
            ("Gaziosmanpasa", "gaziosmanpasa"),
            ("Gungoren", "gungoren"),
            ("Kadikoy", "kadikoy"),
            ("Kagithane", "kagithane"),
            ("Kartal", "kartal"),
            ("Kucukcekmece", "kucukcekmece"),
            ("Maltepe", "maltepe"),
            ("Pendik", "pendik"),
            ("Sancaktepe", "sancaktepe"),
            ("Sariyer", "sariyer"),
            ("Silivri", "silivri"),
            ("Sultanbeyli", "sultanbeyli"),
            ("Sultangazi", "sultangazi"),
            ("Sile", "sile"),
            ("Sisli", "sisli"),
            ("Tuzla", "tuzla"),
            ("Umraniye", "umraniye"),
            ("Uskudar", "uskudar"),
            ("Zeytinburnu", "zeytinburnu"),
        ],
    ),
    "ankara": (
        "Ankara",
        [
            ("Altindag", "altindag"),
            ("Ayas", "ayas"),
            ("Bala", "bala"),
            ("Beypazari", "beypazari"),
            ("Camlidere", "camlidere"),
            ("Cankaya", "cankaya"),
            ("Cubuk", "cubuk"),
            ("Elmadag", "elmadag"),
            ("Etimesgut", "etimesgut"),
            ("Evren", "evren"),
            ("Golbasi", "golbasi"),
            ("Gudul", "gudul"),
            ("Haymana", "haymana"),
            ("Kahramankazan", "kahramankazan"),
            ("Kalecik", "kalecik"),
            ("Kecioren", "kecioren"),
            ("Kizilcahamam", "kizilcahamam"),
            ("Mamak", "mamak"),
            ("Nallihan", "nallihan"),
            ("Polatli", "polatli"),
            ("Pursaklar", "pursaklar"),
            ("Sincan", "sincan"),
            ("Sereflikochisar", "sereflikochisar"),
            ("Yenimahalle", "yenimahalle"),
        ],
    ),
    "izmir": (
        "\u0130zmir",
        [
            ("Aliaga", "aliaga"),
            ("Balcova", "balcova"),
            ("Bayindir", "bayindir"),
            ("Bayrakli", "bayrakli"),
            ("Bergama", "bergama"),
            ("Beydag", "beydag"),
            ("Bornova", "bornova"),
            ("Buca", "buca"),
            ("Cesme", "cesme"),
            ("Cigli", "cigli"),
            ("Dikili", "dikili"),
            ("Foca", "foca"),
            ("Gaziemir", "gaziemir"),
            ("Guzelbahce", "guzelbahce"),
            ("Karabaglar", "karabaglar"),
            ("Karaburun", "karaburun"),
            ("Karsiyaka", "karsiyaka"),
            ("Kemalpasa", "kemalpasa"),
            ("Kinik", "kinik"),
            ("Kiraz", "kiraz"),
            ("Konak", "konak"),
            ("Menderes", "menderes"),
            ("Menemen", "menemen"),
            ("Narlidere", "narlidere"),
            ("Odemis", "odemis"),
            ("Seferihisar", "seferihisar"),
            ("Selcuk", "selcuk"),
            ("Tire", "tire"),
            ("Torbali", "torbali"),
            ("Urla", "urla"),
        ],
    ),
    "mersin": (
        "Mersin",
        [
            ("Akdeniz", "akdeniz"),
            ("Anamur", "anamur"),
            ("Aydincik", "aydincik"),
            ("Bozyazi", "bozyazi"),
            ("Camliyayla", "camliyayla"),
            ("Erdemli", "erdemli"),
            ("Gulnar", "gulnar"),
            ("Mezitli", "mezitli"),
            ("Mut", "mut"),
            ("Silifke", "silifke"),
            ("Tarsus", "tarsus"),
            ("Toroslar", "toroslar"),
            ("Yenisehir", "yenisehir"),
        ],
    ),
    "konya": (
        "Konya",
        [
            ("Ahirli", "ahirli"),
            ("Akoren", "akoren"),
            ("Aksehir", "aksehir"),
            ("Altinekin", "altinekin"),
            ("Beysehir", "beysehir"),
            ("Bozkir", "bozkir"),
            ("Cihanbeyli", "cihanbeyli"),
            ("Celtik", "celtik"),
            ("Cumra", "cumra"),
            ("Derbent", "derbent"),
            ("Derebucak", "derebucak"),
            ("Doganhisar", "doganhisar"),
            ("Emirgazi", "emirgazi"),
            ("Eregli", "eregli"),
            ("Guneysinir", "guneysinir"),
            ("Hadim", "hadim"),
            ("Halkapinar", "halkapinar"),
            ("Huyuk", "huyuk"),
            ("Ilgin", "ilgin"),
            ("Kadinhani", "kadinhani"),
            ("Karapinar", "karapinar"),
            ("Karatay", "karatay"),
            ("Kulu", "kulu"),
            ("Meram", "meram"),
            ("Sarayonu", "sarayonu"),
            ("Selcuklu", "selcuklu"),
            ("Seydisehir", "seydisehir"),
            ("Taskent", "taskent"),
            ("Tuzlukcu", "tuzlukcu"),
            ("Yalihuyuk", "yalihuyuk"),
            ("Yunak", "yunak"),
        ],
    ),
    "mugla": (
        "Mu\u011fla",
        [
            ("Bodrum", "bodrum"),
            ("Dalaman", "dalaman"),
            ("Datca", "datca"),
            ("Fethiye", "fethiye"),
            ("Kavaklidere", "kavaklidere"),
            ("Koycegiz", "koycegiz"),
            ("Marmaris", "marmaris"),
            ("Mentese", "mentese"),
            ("Milas", "milas"),
            ("Ortaca", "ortaca"),
            ("Seydikemer", "seydikemer"),
            ("Ula", "ula"),
            ("Yatagan", "yatagan"),
        ],
    ),
    "sanliurfa": (
        "\u015eanl\u0131urfa",
        [
            ("Akcakale", "akcakale"),
            ("Birecik", "birecik"),
            ("Bozova", "bozova"),
            ("Ceylanpinar", "ceylanpinar"),
            ("Eyyubiye", "eyyubiye"),
            ("Halfeti", "halfeti"),
            ("Haliliye", "haliliye"),
            ("Harran", "harran"),
            ("Hilvan", "hilvan"),
            ("Karakopru", "karakopru"),
            ("Siverek", "siverek"),
            ("Suruc", "suruc"),
            ("Viransehir", "viransehir"),
        ],
    ),
    "trabzon": (
        "Trabzon",
        [
            ("Akcaabat", "akcaabat"),
            ("Arakli", "arakli"),
            ("Arsin", "arsin"),
            ("Besikduzu", "besikduzu"),
            ("Caykara", "caykara"),
            ("Dernekpazari", "dernekpazari"),
            ("Duzkoy", "duzkoy"),
            ("Hayrat", "hayrat"),
            ("Koprubasi", "koprubasi"),
            ("Macka", "macka"),
            ("Of", "of"),
            ("Ortahisar", "ortahisar"),
            ("Salpazari", "salpazari"),
            ("Surmene", "surmene"),
            ("Tonya", "tonya"),
            ("Vakfikebir", "vakfikebir"),
            ("Yomra", "yomra"),
        ],
    ),
    "samsun": (
        "Samsun",
        [
            ("Ondokuzmayis", "ondokuzmayis"),
            ("Alaçam", "alacam"),
            ("Asarcik", "asarcik"),
            ("Atakum", "atakum"),
            ("Ayvacik", "ayvacik"),
            ("Bafra", "bafra"),
            ("Canik", "canik"),
            ("Carsamba", "carsamba"),
            ("Havza", "havza"),
            ("Ilkadim", "ilkadim"),
            ("Kavak", "kavak"),
            ("Ladik", "ladik"),
            ("Salipazari", "salipazari"),
            ("Tekkekoy", "tekkekoy"),
            ("Terme", "terme"),
            ("Vezirkopru", "vezirkopru"),
            ("Yakakent", "yakakent"),
        ],
    ),
    "van": (
        "Van",
        [
            ("Bahcesaray", "bahcesaray"),
            ("Baskale", "baskale"),
            ("Caldiran", "caldiran"),
            ("Catak", "catak"),
            ("Edremit", "edremit"),
            ("Ercis", "ercis"),
            ("Gevas", "gevas"),
            ("Gurpinar", "gurpinar"),
            ("Ipekyolu", "ipekyolu"),
            ("Muradiye", "muradiye"),
            ("Ozalp", "ozalp"),
            ("Saray", "saray"),
            ("Tusba", "tusba"),
        ],
    ),
    "sakarya": (
        "Sakarya",
        [
            ("Adapazari", "adapazari"),
            ("Akyazi", "akyazi"),
            ("Arifiye", "arifiye"),
            ("Erenler", "erenler"),
            ("Ferizli", "ferizli"),
            ("Geyve", "geyve"),
            ("Hendek", "hendek"),
            ("Karapurcek", "karapurcek"),
            ("Karasu", "karasu"),
            ("Kaynarca", "kaynarca"),
            ("Kocaali", "kocaali"),
            ("Pamukova", "pamukova"),
            ("Sapanca", "sapanca"),
            ("Serdivan", "serdivan"),
            ("Sogutlu", "sogutlu"),
            ("Tarakli", "tarakli"),
        ],
    ),
    "bursa": (
        "Bursa",
        [
            ("Buyukorhan", "buyukorhan"),
            ("Gemlik", "gemlik"),
            ("Gursu", "gursu"),
            ("Harmancik", "harmancik"),
            ("Inegol", "inegol"),
            ("Iznik", "iznik"),
            ("Karacabey", "karacabey"),
            ("Keles", "keles"),
            ("Kestel", "kestel"),
            ("Mudanya", "mudanya"),
            ("Mustafakemalpasa", "mustafakemalpasa"),
            ("Nilufer", "nilufer"),
            ("Orhaneli", "orhaneli"),
            ("Orhangazi", "orhangazi"),
            ("Osmangazi", "osmangazi"),
            ("Yenisehir", "yenisehir"),
            ("Yildirim", "yildirim"),
        ],
    ),
}


def build_segments(city_filter: str | None = None, district_filter: str | None = None) -> list[DistrictSegment]:
    city_filter_normalized = city_filter.casefold() if city_filter else None
    district_filter_normalized = district_filter.casefold() if district_filter else None
    segments: list[DistrictSegment] = []
    for city_slug, (city_name, districts) in RAW_DISTRICTS.items():
        if city_filter_normalized and city_filter_normalized not in {city_slug.casefold(), city_name.casefold()}:
            continue
        for district_name, district_slug in districts:
            if district_filter_normalized and district_filter_normalized not in {
                district_slug.casefold(),
                district_name.casefold(),
            }:
                continue
            segments.append(
                DistrictSegment(
                    city_name=city_name,
                    city_slug=city_slug,
                    district_name=district_name,
                    district_slug=district_slug,
                )
            )
    return segments


def load_checkpoint(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"segment_index": 0, "offset": 0, "completed": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_checkpoint(path: Path, *, segment_index: int, offset: int, completed: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"segment_index": segment_index, "offset": offset, "completed": completed}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_url(segment: DistrictSegment, offset: int, page_size: int) -> str:
    parsed = urlparse(segment.url_base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({"pagingSize": str(page_size), "pagingOffset": str(offset)})
    return urlunparse(parsed._replace(query=urlencode(query)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape dense Sahibinden city pages district by district.")
    parser.add_argument("--city", default=None, help="Optional city: istanbul, ankara, izmir, bursa")
    parser.add_argument("--district", default=None, help="Optional district slug/name, e.g. esenyurt")
    parser.add_argument("--districts", default=None, help="Comma-separated district slugs/names, e.g. esenyurt,pendik")
    parser.add_argument("--district-limit", type=int, default=None)
    parser.add_argument("--page-size", type=int, default=50, choices=[20, 50])
    parser.add_argument("--pages-per-district", type=int, default=300, help="Use 0 to keep going until the site ends.")
    parser.add_argument("--delay-min", type=float, default=4.0)
    parser.add_argument("--delay-max", type=float, default=8.0)
    parser.add_argument("--manual-wait-seconds", type=float, default=120)
    parser.add_argument(
        "--max-stale-pages",
        type=int,
        default=5,
        help="Move to the next district after this many consecutive pages add no new listings.",
    )
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument("--stop-on-access", action="store_true")
    parser.add_argument("--skip-completed", action="store_true")
    return parser


async def run(args: argparse.Namespace) -> None:
    checkpoint_path = Path(args.checkpoint_path)
    if args.reset_checkpoint and checkpoint_path.exists():
        checkpoint_path.unlink()

    checkpoint = load_checkpoint(checkpoint_path)
    completed = [str(item) for item in checkpoint.get("completed", [])]
    if args.districts:
        requested_districts = {item.strip().casefold() for item in args.districts.split(",") if item.strip()}
        segments = [
            segment
            for segment in build_segments(args.city, None)
            if segment.district_slug.casefold() in requested_districts
            or segment.district_name.casefold() in requested_districts
        ]
        found_districts = {segment.district_slug.casefold() for segment in segments}
        missing_districts = sorted(requested_districts - found_districts)
        if missing_districts:
            print(f"Warning: district filters not matched: {', '.join(missing_districts)}", flush=True)
    else:
        segments = build_segments(args.city, args.district)
    if args.district_limit is not None:
        segments = segments[: args.district_limit]
    if not segments:
        raise SystemExit("No district segment matched the requested filters.")

    segment_index = int(checkpoint.get("segment_index", 0)) if not (args.city or args.district) else 0
    offset = int(checkpoint.get("offset", 0)) if not (args.city or args.district) else 0

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
        if args.skip_completed:
            segments = [
                segment
                for segment in segments
                if segment.key not in completed
                and f"{segment.key} (empty)" not in completed
                and f"{segment.key} (skipped)" not in completed
            ]
            segment_index = 0
            offset = 0
            if not segments:
                print("No pending district segment remains after skipping completed entries.", flush=True)
                return

        segments = segments[segment_index:]
        print(
            f"Starting district segmented scrape. segments_remaining={len(segments)} "
            f"segment_index={segment_index} offset={offset} pages_per_district={args.pages_per_district}",
            flush=True,
        )

        for relative_index, segment in enumerate(segments):
            absolute_index = segment_index + relative_index
            current_offset = offset if relative_index == 0 else 0
            segment_had_data = False
            total_count = None
            stale_pages = 0

            print(f"\nDistrict {absolute_index + 1}: {segment.city_name} / {segment.district_name} ({segment.url_base})", flush=True)
            max_pages = args.pages_per_district if args.pages_per_district > 0 else 1_000_000
            for page_index in range(1, max_pages + 1):
                url = build_url(segment, current_offset, args.page_size)
                print(f"Opening {url}", flush=True)
                tab = await driver.get(url)
                await wait_for_manual_access_check(tab, config, f"opening {segment.key} offset {current_offset}")
                html = await tab.get_content()
                if total_count is None:
                    total_count = extract_total_count(html)
                    print(f"reported_total_count={total_count}", flush=True)

                try:
                    result = store_html_page(
                        html,
                        current_offset,
                        args.page_size,
                        args.db_path,
                        city_override=segment.city_name,
                        district_override=segment.district_name,
                    )
                except RuntimeError as exc:
                    print(f"EMPTY/STOP district={segment.key} offset={current_offset} error={exc}", flush=True)
                    if has_login_page(html) or has_access_challenge(html):
                        save_checkpoint(
                            checkpoint_path,
                            segment_index=absolute_index,
                            offset=current_offset,
                            completed=completed,
                        )
                        print(f"Access/login page detected for {segment.key}; keeping it pending.", flush=True)
                        if args.stop_on_access:
                            return
                        break

                    print(f"No listing rows found on a normal page for {segment.key}; treating district as complete.", flush=True)
                    segment_had_data = segment_had_data or current_offset > 0
                    break

                segment_had_data = True
                next_offset = current_offset + args.page_size
                save_checkpoint(
                    checkpoint_path,
                    segment_index=absolute_index,
                    offset=next_offset,
                    completed=completed,
                )
                print(
                    f"district={segment.key} page={page_index} offset={result.offset} "
                    f"parsed={result.parsed} changed={result.changed} stored_total={result.stored_total} "
                    f"next_offset={next_offset} total_count={total_count}",
                    flush=True,
                )
                current_offset = next_offset

                if result.changed == 0:
                    stale_pages += 1
                    if args.max_stale_pages > 0 and stale_pages >= args.max_stale_pages:
                        print(
                            f"No new listings for {stale_pages} consecutive pages; moving to next district.",
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
                skipped_marker = f"{segment.key} (empty)"
                if skipped_marker not in completed:
                    completed.append(skipped_marker)
            save_checkpoint(checkpoint_path, segment_index=absolute_index + 1, offset=0, completed=completed)
    finally:
        driver.stop()


def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
