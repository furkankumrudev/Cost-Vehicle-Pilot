"""Streamlit interface for ArabamFiyat.com."""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import streamlit as st

from src.analysis.market_engine import build_market_analysis

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "runtime" / "vehicle_listings.sqlite3"
CATALOG_PATH = PROJECT_ROOT / "data" / "reference" / "vehicle_catalog.json"
ALL_OPTION = "Tümü"
MIN_SAMPLE_SIZE = 8

TURKISH_MONTHS = {
    "ocak": 1,
    "subat": 2,
    "şubat": 2,
    "mart": 3,
    "nisan": 4,
    "mayis": 5,
    "mayıs": 5,
    "haziran": 6,
    "temmuz": 7,
    "agustos": 8,
    "ağustos": 8,
    "eylul": 9,
    "eylül": 9,
    "ekim": 10,
    "kasim": 11,
    "kasım": 11,
    "aralik": 12,
    "aralık": 12,
}

BRAND_ALIASES = {
    "mercedesbenz": "Mercedes-Benz",
    "tofa": "Tofaş",
    "tofas": "Tofaş",
    "tofat": "Tofaş",
}


st.set_page_config(
    page_title="ArabamFiyat.com",
    page_icon="AF",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    :root {
        --cvp-ink: #f4f7fb;
        --cvp-muted: #a7b0bf;
        --cvp-line: #334155;
        --cvp-panel: #161d27;
        --cvp-panel-soft: #1d2633;
        --cvp-blue: #6ea8fe;
        --cvp-teal: #49d0b8;
        --cvp-red: #ff8a7a;
        --cvp-soft: #101722;
    }

    .stApp {
        background: #0f141c;
        color: var(--cvp-ink);
    }

    [data-testid="stSidebar"] {
        background: #121923;
        border-right: 1px solid var(--cvp-line);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1440px;
    }

    .cvp-topbar {
        border: 1px solid var(--cvp-line);
        border-radius: 8px;
        background: linear-gradient(135deg, #151d28 0%, #101722 58%, #17231f 100%);
        padding: 1.1rem 1.2rem;
        margin-bottom: 1.25rem;
    }

    .cvp-title {
        font-size: 1.8rem;
        line-height: 1.2;
        font-weight: 750;
        letter-spacing: 0;
        color: var(--cvp-ink);
        margin: 0;
    }

    .cvp-subtitle {
        color: var(--cvp-muted);
        font-size: 0.98rem;
        margin-top: 0.35rem;
        max-width: 920px;
    }

    .cvp-panel {
        background: var(--cvp-panel);
        border: 1px solid var(--cvp-line);
        border-radius: 8px;
        padding: 1rem;
        min-height: 100%;
    }

    .cvp-kicker {
        color: var(--cvp-muted);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .cvp-range {
        font-size: 1.85rem;
        line-height: 1.15;
        font-weight: 800;
        color: var(--cvp-blue);
        margin-bottom: 0.35rem;
    }

    .cvp-copy {
        color: var(--cvp-muted);
        font-size: 0.92rem;
        line-height: 1.45;
    }

    div[data-testid="stMetric"] {
        background: var(--cvp-panel);
        border: 1px solid var(--cvp-line);
        border-radius: 8px;
        padding: 0.85rem 0.95rem;
        min-height: 105px;
    }

    div[data-testid="stMetricLabel"] {
        color: var(--cvp-muted);
        font-weight: 650;
    }

    div[data-testid="stMetricValue"] {
        color: var(--cvp-ink);
        font-size: 1.45rem;
    }

    div[data-testid="stMarkdownContainer"],
    .st-emotion-cache-ue6h4q,
    .st-emotion-cache-16idsys p,
    label,
    .stCaptionContainer {
        color: var(--cvp-muted);
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--cvp-ink);
    }

    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {
        background: var(--cvp-panel-soft);
        border-color: var(--cvp-line);
        color: var(--cvp-ink);
    }

    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        color: var(--cvp-ink);
    }

    .stButton > button {
        border-radius: 6px;
        min-height: 2.8rem;
        font-weight: 700;
        border: 1px solid #6ea8fe;
        background: #255a9b;
        color: #ffffff;
    }

    .stButton > button:hover {
        border-color: #9bc2ff;
        background: #326db8;
        color: #ffffff;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--cvp-line);
        border-radius: 8px;
    }

    div[data-testid="stAlert"] {
        background: #201c12;
        color: #f7df9e;
        border: 1px solid #7c5d1e;
    }
</style>
"""


def format_try(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{int(round(value)):,.0f} TL".replace(",", ".")


@st.cache_data(show_spinner=False)
def load_vehicle_catalog(path: str, file_mtime: float | None = None) -> dict[str, object]:
    catalog_path = Path(path)
    if not catalog_path.exists():
        return {"brands": []}
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def normalize_option_key(value: object) -> str:
    text = str(value or "").strip().casefold()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", text)


def parse_listing_date(value: object) -> pd.Timestamp | None:
    text = str(value or "").strip()
    if not text:
        return None

    folded = text.casefold()
    today = date.today()
    if folded in {"bugün", "bugun"}:
        return pd.Timestamp(today)
    if folded == "dün" or folded == "dun":
        return pd.Timestamp(today - timedelta(days=1))

    match = re.search(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})", text)
    if match:
        day = int(match.group(1))
        month_key = match.group(2).casefold()
        month = TURKISH_MONTHS.get(month_key)
        year = int(match.group(3))
        if month:
            try:
                return pd.Timestamp(date(year, month, day))
            except ValueError:
                return None

    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return None
    return pd.Timestamp(parsed).normalize()


def canonical_brand_name(value: object) -> str:
    text = str(value or "").strip()
    return BRAND_ALIASES.get(normalize_option_key(text), text)


def canonical_series_name(value: object, brand: str) -> str:
    text = str(value or "").strip()
    if normalize_option_key(brand) == "mercedesbenz" and len(text) == 1 and text.isalpha():
        return f"{text.upper()} Serisi"
    return text


def series_filter_values(series: str) -> list[str]:
    values = [series]
    if series.endswith(" Serisi"):
        prefix = series.removesuffix(" Serisi").strip()
        if len(prefix) == 1 and prefix.isalpha():
            values.append(prefix)
    elif len(series) == 1 and series.isalpha():
        values.append(f"{series.upper()} Serisi")
    return values


def merge_options(*option_groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for options in option_groups:
        for option in options:
            label = canonical_brand_name(option)
            key = normalize_option_key(label)
            if not label or key in seen:
                continue
            seen.add(key)
            merged.append(label)
    return merged


def catalog_brand_options(catalog: dict[str, object]) -> list[str]:
    brands = catalog.get("brands", [])
    if not isinstance(brands, list):
        return []
    return merge_options([str(item["name"]) for item in brands if isinstance(item, dict) and item.get("name")])


def find_catalog_brand(catalog: dict[str, object], brand: str) -> dict[str, object] | None:
    brands = catalog.get("brands", [])
    if not isinstance(brands, list):
        return None

    target_key = normalize_option_key(brand)
    for item in brands:
        if not isinstance(item, dict):
            continue
        item_name = item.get("name")
        if normalize_option_key(canonical_brand_name(item_name)) == target_key:
            return item
    return None


def catalog_series_options(catalog: dict[str, object], brand: str) -> list[str]:
    if brand == ALL_OPTION:
        return []
    item = find_catalog_brand(catalog, brand)
    if item is None:
        return []
    series = item.get("series", [])
    if not isinstance(series, list):
        return []
    return [
        canonical_series_name(series_item["name"], brand)
        for series_item in series
        if isinstance(series_item, dict) and series_item.get("name")
    ]


def catalog_model_options(catalog: dict[str, object], brand: str, series: str) -> list[str]:
    if brand == ALL_OPTION or series == ALL_OPTION:
        return []
    item = find_catalog_brand(catalog, brand)
    if item is None:
        return []
    series_items = item.get("series", [])
    if not isinstance(series_items, list):
        return []
    for series_item in series_items:
        if not isinstance(series_item, dict) or not series_item.get("name"):
            continue
        catalog_series_name = str(series_item["name"])
        if catalog_series_name == series or canonical_series_name(catalog_series_name, brand) == series:
            models = series_item.get("models", [])
            if not isinstance(models, list):
                return []
            return [str(model) for model in models if model]
    return []


@st.cache_data(show_spinner="İlan verileri yükleniyor...", ttl=300)
def load_listings(db_path: str) -> pd.DataFrame:
    """İlan verilerini SQLite'tan okur.

    Sağlamlık notları:
    - DB dosyası yoksa ya da beklenen tablolardan hiçbiri yoksa (ör. scraper
      henüz hiç çalıştırılmadıysa) uygulamayı ÇÖKERTMEK yerine boş bir
      DataFrame döner; arayüz bunu "veri bekleniyor" ekranıyla karşılar.
    - ttl=300: arka planda scraper yeni veri eklediğinde, önbellek en fazla
      5 dakika içinde otomatik yenilenir (uygulamayı yeniden başlatmaya
      gerek kalmaz).
    """
    path = Path(db_path)
    if not path.exists():
        return pd.DataFrame()

    candidate_tables = ["vehicle_listings_clean", "vehicle_listings"]

    try:
        with sqlite3.connect(path) as connection:
            existing_tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            table_name = next((t for t in candidate_tables if t in existing_tables), None)
            if table_name is None:
                st.warning(
                    "Veritabanında beklenen ilan tablosu bulunamadı "
                    f"({' / '.join(candidate_tables)}). Scraper/ETL adımının "
                    "çalıştırıldığından emin olun."
                )
                return pd.DataFrame()

            df = pd.read_sql_query(
                f"""
                SELECT
                    title,
                    brand,
                    series,
                    model,
                    year,
                    mileage_km,
                    transmission,
                    fuel_type,
                    body_type,
                    color,
                    city,
                    district,
                    seller_type,
                    price,
                    currency,
                    listing_date,
                    listing_url,
                    scraped_at
                FROM {table_name}
                WHERE price IS NOT NULL
                """,
                connection,
            )
    except sqlite3.DatabaseError as exc:
        st.error(f"Veritabanı okunurken hata oluştu: {exc}")
        return pd.DataFrame()

    numeric_columns = ["year", "mileage_km", "price"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["parsed_listing_date"] = df["listing_date"].map(parse_listing_date)
    return df


def unique_options(df: pd.DataFrame, column: str) -> list[str]:
    if df.empty or column not in df:
        return []
    values = df[column].dropna().astype(str).str.strip()
    values = values[values.ne("")]
    return sorted(values.unique().tolist())


def filter_by_series(df: pd.DataFrame, series: str) -> pd.DataFrame:
    if df.empty or series == ALL_OPTION:
        return df

    series_values = df["series"].fillna("")
    missing_series = series_values.str.strip().eq("")
    series_values_folded = series_values.str.casefold()
    series_values_to_match = series_filter_values(series)
    series_mask = series_values_folded.isin([value.casefold() for value in series_values_to_match])
    title_mask = pd.Series(False, index=df.index)
    for value in series_values_to_match:
        value = value.strip()
        if not value:
            continue
        pattern = rf"(?<!\w){re.escape(value)}(?!\w)"
        series_mask = series_mask | series_values.str.contains(pattern, case=False, na=False, regex=True)
        title_mask = title_mask | df["title"].fillna("").str.contains(pattern, case=False, na=False, regex=True)
    return df[series_mask | (missing_series & title_mask)]


def apply_filters(
    df: pd.DataFrame,
    brand: str,
    series: str,
    model: str,
    year_range: tuple[int, int],
    mileage_max: int,
) -> pd.DataFrame:
    if df.empty:
        return df

    filtered = df.copy()
    if brand != ALL_OPTION:
        brand_key = normalize_option_key(brand)
        filtered = filtered[filtered["brand"].fillna("").map(normalize_option_key) == brand_key]
    filtered = filter_by_series(filtered, series)
    if model != ALL_OPTION:
        model_mask = filtered["model"].fillna("").str.contains(model, case=False, na=False, regex=False)
        series_mask = filtered["series"].fillna("").str.contains(model, case=False, na=False, regex=False)
        title_mask = filtered["title"].fillna("").str.contains(model, case=False, na=False, regex=False)
        filtered = filtered[model_mask | series_mask | title_mask]
    min_year, max_year = year_range
    filtered = filtered[(filtered["year"].isna()) | (filtered["year"].between(min_year, max_year))]
    filtered = filtered[(filtered["mileage_km"].isna()) | (filtered["mileage_km"] <= mileage_max)]
    return filtered


def price_summary(df: pd.DataFrame) -> dict[str, float | int]:
    prices = df["price"].dropna()
    if prices.empty:
        return {}

    q1 = prices.quantile(0.25)
    median = prices.quantile(0.50)
    q3 = prices.quantile(0.75)
    return {
        "count": int(prices.count()),
        "min": float(prices.min()),
        "q1": float(q1),
        "median": float(median),
        "q3": float(q3),
        "max": float(prices.max()),
        "mean": float(prices.mean()),
    }


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="cvp-panel">
            <div class="cvp-kicker">Veri bekleniyor</div>
            <div class="cvp-range">Henüz analiz edilecek ilan yok</div>
            <div class="cvp-copy">
                Güncel ilan verileri SQLite veritabanına aktarıldığında bu ekran fiyat aralığı,
                dağılım grafiği ve benzer ilan karşılaştırmasını otomatik gösterecek.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_price_distribution(df: pd.DataFrame, summary: dict[str, float | int]) -> None:
    fig = px.histogram(
        df,
        x="price",
        nbins=24,
        color_discrete_sequence=["#2357a6"],
        labels={"price": "Fiyat"},
    )
    fig.add_vline(
        x=summary["median"],
        line_width=2,
        line_dash="dash",
        line_color="#0f766e",
        annotation_text="Medyan",
        annotation_position="top right",
    )
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=20, b=10),
        bargap=0.08,
        paper_bgcolor="#161d27",
        plot_bgcolor="#161d27",
        yaxis_title="İlan sayısı",
        xaxis_title="Fiyat (TL)",
        font=dict(color="#f4f7fb"),
    )
    st.plotly_chart(fig, width="stretch")


def compute_trend_line(x: pd.Series, y: pd.Series) -> tuple[np.ndarray, np.ndarray] | None:
    """Basit doğrusal regresyon (en küçük kareler) ile trend çizgisi üretir.

    statsmodels gibi ek bir bağımlılık gerektirmeden (numpy zaten pandas'ın
    bağımlılığı olduğu için ekstra kurulum gerekmez) px.scatter(trendline="ols")
    ile aynı işi görür.
    """
    valid = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(valid) < 3 or valid["x"].nunique() < 2:
        return None
    slope, intercept = np.polyfit(valid["x"], valid["y"], 1)
    x_line = np.linspace(valid["x"].min(), valid["x"].max(), 50)
    y_line = slope * x_line + intercept
    return x_line, y_line


def render_price_by_year(df: pd.DataFrame) -> None:
    plot_df = df.dropna(subset=["year", "price"])
    if plot_df.empty:
        st.info("Yıl bilgisi olan yeterli ilan bulunamadı.")
        return

    fig = px.scatter(
        plot_df,
        x="year",
        y="price",
        size="price",
        hover_data=["title", "mileage_km", "city"],
        color_discrete_sequence=["#0f766e"],
        labels={"year": "Model yılı", "price": "Fiyat"},
    )

    trend = compute_trend_line(plot_df["year"], plot_df["price"])
    if trend is not None:
        x_line, y_line = trend
        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                name="Trend",
                line=dict(color="#ff8a7a", width=2, dash="dot"),
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="#161d27",
        plot_bgcolor="#161d27",
        yaxis_title="Fiyat (TL)",
        xaxis_title="Model yılı",
        font=dict(color="#f4f7fb"),
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")


def render_price_by_mileage(df: pd.DataFrame) -> None:
    """Kilometre arttıkça fiyatın nasıl azaldığını gösterir (amortisman eğrisi)."""
    plot_df = df.dropna(subset=["mileage_km", "price"])
    if plot_df.empty:
        st.info("Kilometre bilgisi olan yeterli ilan bulunamadı.")
        return

    fig = px.scatter(
        plot_df,
        x="mileage_km",
        y="price",
        hover_data=["title", "year", "city"],
        color_discrete_sequence=["#6ea8fe"],
        labels={"mileage_km": "Kilometre", "price": "Fiyat"},
    )

    trend = compute_trend_line(plot_df["mileage_km"], plot_df["price"])
    if trend is not None:
        x_line, y_line = trend
        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                name="Trend",
                line=dict(color="#ff8a7a", width=2, dash="dot"),
                hoverinfo="skip",
            )
        )
        # Trend eğiminden "her 10.000 km'de ortalama fiyat kaybı" bilgisini çıkarıp gösterelim
        slope = (y_line[-1] - y_line[0]) / (x_line[-1] - x_line[0]) if x_line[-1] != x_line[0] else 0
        loss_per_10k = slope * 10000
        if loss_per_10k < 0:
            st.caption(f"Trend: Her 10.000 km'de ortalama **{format_try(abs(loss_per_10k))}** değer kaybı.")
        else:
            st.caption("Trend: Bu filtrelerde kilometre ile fiyat arasında belirgin bir düşüş görünmüyor.")

    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="#161d27",
        plot_bgcolor="#161d27",
        yaxis_title="Fiyat (TL)",
        xaxis_title="Kilometre",
        font=dict(color="#f4f7fb"),
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")


def render_market_gauge(summary: dict[str, float | int]) -> None:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=summary["median"],
            number={"valueformat": ",.0f", "suffix": " TL"},
            gauge={
                "axis": {"range": [summary["min"], summary["max"]]},
                "bar": {"color": "#2357a6"},
                "steps": [
                    {"range": [summary["min"], summary["q1"]], "color": "#e8f3f0"},
                    {"range": [summary["q1"], summary["q3"]], "color": "#dbeafe"},
                    {"range": [summary["q3"], summary["max"]], "color": "#fde8e4"},
                ],
                "threshold": {
                    "line": {"color": "#0f766e", "width": 4},
                    "thickness": 0.75,
                    "value": summary["median"],
                },
            },
        )
    )
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=25, b=10),
        paper_bgcolor="#161d27",
        font=dict(color="#f4f7fb"),
    )
    st.plotly_chart(fig, width="stretch")


def render_listing_date_price_trend(df: pd.DataFrame) -> None:
    trend_df = df.dropna(subset=["price"]).copy()
    if trend_df.empty or "listing_date" not in trend_df:
        st.info("Tarih bazlı fiyat trendi için yeterli veri yok.")
        return

    trend_df["date"] = trend_df["listing_date"].map(parse_listing_date)
    trend_df = trend_df.dropna(subset=["date"])
    if trend_df["date"].nunique() < 2:
        st.info("Fiyat trendi için en az iki farklı ilan tarihi gerekiyor.")
        return

    daily = (
        trend_df.groupby("date", as_index=False)
        .agg(
            median_price=("price", "median"),
            mean_price=("price", "mean"),
            listing_count=("price", "size"),
        )
        .sort_values("date")
    )
    if len(daily) < 2:
        st.info("Fiyat trendi için yeterli tarihli veri yok.")
        return

    first_price = float(daily["median_price"].iloc[0])
    last_price = float(daily["median_price"].iloc[-1])
    change = last_price - first_price
    change_pct = (change / first_price * 100) if first_price else 0

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["median_price"],
            mode="lines+markers",
            name="Medyan fiyat",
            line=dict(color="#6ea8fe", width=3),
            marker=dict(size=7),
            hovertemplate="%{x|%d.%m.%Y}<br>Medyan: %{y:,.0f} TL<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["mean_price"],
            mode="lines",
            name="Ortalama fiyat",
            line=dict(color="#ff8a7a", width=2, dash="dot"),
            hovertemplate="%{x|%d.%m.%Y}<br>Ortalama: %{y:,.0f} TL<extra></extra>",
        )
    )
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="#161d27",
        plot_bgcolor="#161d27",
        yaxis_title="Fiyat (TL)",
        xaxis_title="İlan tarihi",
        font=dict(color="#f4f7fb"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig, width="stretch")

    direction = "artmış" if change > 0 else "azalmış" if change < 0 else "sabit kalmış"
    st.caption(
        f"{daily['date'].dt.strftime('%d.%m.%Y').iloc[0]} - "
        f"{daily['date'].dt.strftime('%d.%m.%Y').iloc[-1]} arasında medyan fiyat "
        f"{format_try(abs(change))} ({abs(change_pct):.1f}%) {direction}. "
        f"Bu trend {int(daily['listing_count'].sum())} benzer ilan üzerinden hesaplandı."
    )


def render_available_listings(filtered: pd.DataFrame) -> None:
    """Show raw listings when the price-range sample is still too small."""
    if filtered.empty:
        return

    listing_table = filtered[
        ["title", "brand", "series", "year", "mileage_km", "city", "price", "listing_url"]
    ].sort_values("price")
    listing_table = listing_table.rename(
        columns={
            "title": "İlan",
            "brand": "Marka",
            "series": "Seri",
            "year": "Yıl",
            "mileage_km": "Kilometre",
            "city": "Şehir",
            "price": "Fiyat",
            "listing_url": "Bağlantı",
        }
    )
    st.dataframe(
        listing_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Fiyat": st.column_config.NumberColumn(format="%d TL"),
            "Kilometre": st.column_config.NumberColumn(format="%d km"),
            "Bağlantı": st.column_config.LinkColumn(display_text="İlana git"),
        },
    )


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    df = load_listings(str(DB_PATH))
    catalog = load_vehicle_catalog(str(CATALOG_PATH), CATALOG_PATH.stat().st_mtime if CATALOG_PATH.exists() else None)

    st.markdown(
        """
        <div class="cvp-topbar">
            <h1 class="cvp-title">ArabamFiyat.com</h1>
            <div class="cvp-subtitle">
                Güncel ilan verilerinden benzer araçları analiz eden fiyat aralığı ve piyasa dağılım ekranı.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.subheader("Araç Özellikleri")

        catalog_brands = catalog_brand_options(catalog)
        brand_options = [ALL_OPTION] + merge_options(catalog_brands, unique_options(df, "brand"))
        brand = st.selectbox("Marka", brand_options, index=0)

        catalog_series = catalog_series_options(catalog, brand)
        if brand == ALL_OPTION:
            series_source = df
        else:
            brand_key = normalize_option_key(brand)
            series_source = df[df["brand"].fillna("").map(normalize_option_key) == brand_key]
        series_options = [ALL_OPTION] + merge_options(catalog_series, unique_options(series_source, "series"))
        series = st.selectbox("Seri / Model", series_options, index=0)

        catalog_models = catalog_model_options(catalog, brand, series)
        model_source = filter_by_series(series_source, series)
        database_models = unique_options(model_source, "model")
        model_options = [ALL_OPTION] + (database_models or catalog_models)
        selected_model = st.selectbox("Model / Paket", model_options, index=0)

        # A selected older series (for example Brera) should not be hidden by the
        # generic 2015+ defaults used for the full marketplace view.
        selection_source = model_source if series != ALL_OPTION and not model_source.empty else df
        year_values = selection_source["year"].dropna() if not selection_source.empty else pd.Series(dtype="float64")
        min_year = int(year_values.min()) if not year_values.empty else 2000
        max_year = int(year_values.max()) if not year_values.empty else 2026
        default_min_year = min_year if series != ALL_OPTION else max(min_year, 2015)
        slider_max_year = max_year if max_year > min_year else min_year + 1
        year_range = st.slider("Model yılı", min_year, slider_max_year, (default_min_year, max_year))

        mileage_values = (
            selection_source["mileage_km"].dropna()
            if not selection_source.empty
            else pd.Series(dtype="float64")
        )
        max_mileage = int(max(mileage_values.max(), 100000)) if not mileage_values.empty else 300000
        default_mileage = max_mileage if series != ALL_OPTION else min(max_mileage, 250000)
        mileage_max = st.slider("Maksimum kilometre", 0, max_mileage, default_mileage, step=5000)
        user_price = st.number_input(
            "Aracınızın fiyatı (opsiyonel)",
            min_value=0,
            value=0,
            step=10000,
            format="%d",
        )

        st.divider()
        analyze_clicked = st.button("Mevcut Veriden Analiz Et", width="stretch")
        st.caption(f"Veritabanı: {DB_PATH.as_posix()}")
        if catalog_brands:
            st.caption(
                f"Katalog: {catalog.get('brand_count', len(catalog_brands))} marka, "
                f"{catalog.get('series_count', 0)} seri"
            )

    # session_state ile "analiz edildi" durumunu kalıcı tutuyoruz. Böylece
    # kullanıcı butona bastıktan SONRA yıl/km slider'ını oynatsa bile sonuçlar
    # tekrar gizlenmiyor; her filtre değişikliğinde otomatik güncelleniyor.
    # Yeni bir analiz turu her zaman butona basarak başlatılır.
    if "analyzed" not in st.session_state:
        st.session_state["analyzed"] = False
    if analyze_clicked:
        st.session_state["analyzed"] = True
    analyze = st.session_state["analyzed"]

    if analyze:
        if brand == ALL_OPTION or series == ALL_OPTION:
            st.warning("Analiz için önce marka ve seri seç.")
            analyze = False

    if df.empty:
        render_empty_state()
        return

    filtered = apply_filters(df, brand, series, selected_model, year_range, mileage_max)
    target_year = int(round((year_range[0] + year_range[1]) / 2))
    analysis = build_market_analysis(
        filtered,
        target_year=target_year,
        target_mileage=mileage_max,
        selected_model=None if selected_model == ALL_OPTION else selected_model,
        user_price=int(user_price) if user_price else None,
    )
    summary = analysis.get("summary", {})
    market_df = analysis.get("used_listings", filtered)
    if not isinstance(market_df, pd.DataFrame):
        market_df = filtered

    if not analyze:
        st.markdown(
            """
            <div class="cvp-panel">
                <div class="cvp-kicker">Hazır</div>
                <div class="cvp-range">Piyasa aralığını öğren</div>
                <div class="cvp-copy">
                    Sol taraftan marka, seri, model yılı ve kilometre bilgisini seç.
                    Analiz başlatıldığında benzer ilanların fiyat yoğunluğu, medyan değeri ve önerilen piyasa aralığı hesaplanır.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if not summary or int(analysis.get("count", 0)) < MIN_SAMPLE_SIZE:
        st.warning("Bu filtrelerle yeterli benzer ilan bulunamadı. Filtreleri biraz genişlet.")
        st.metric("Eşleşen ilan", len(filtered))
        if not filtered.empty:
            st.caption(
                f"Fiyat aralığı için en az {MIN_SAMPLE_SIZE} ilan gerekir; "
                "bulunan ilanlar aşağıda gösteriliyor."
            )
            st.subheader("Bulunan İlanlar")
            render_available_listings(filtered)
        return

    range_low = summary.get("weighted_q1", summary["q1"])
    range_high = summary.get("weighted_q3", summary["q3"])
    median_price = summary.get("weighted_median", summary["median"])
    confidence = str(analysis.get("confidence", "-"))
    outlier_count = int(analysis.get("outlier_count", 0))
    total_match_count = len(filtered)
    used_count = int(analysis.get("used_count", summary["count"]))
    market_position = analysis.get("market_position")
    price_delta_pct = analysis.get("price_delta_pct")
    position_text = ""
    if market_position and price_delta_pct is not None:
        position_text = (
            f" Girilen fiyat medyana gore %{abs(float(price_delta_pct)):.1f} "
            f"{'yukarida' if float(price_delta_pct) > 0 else 'asagida'}; yorum: {market_position}."
        )

    st.markdown(
        f"""
        <div class="cvp-panel">
            <div class="cvp-kicker">Akıllı piyasa aralığı</div>
            <div class="cvp-range">{format_try(range_low)} - {format_try(range_high)}</div>
            <div class="cvp-copy">
                Veritabanında {total_match_count:,} ilan eşleşti; fiyat hesabında en yakın {used_count} ilan
                yıl/kilometre/model yakınlığına göre ağırlıklandırıldı. Ağırlıklı medyan piyasa değeri {format_try(median_price)}.
                Güven seviyesi: {confidence}. {outlier_count} uç fiyat analiz dışı bırakıldı.{position_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(5)
    metric_cols[0].metric("Toplam eşleşen", f"{total_match_count:,}".replace(",", "."))
    metric_cols[1].metric("Analizde kullanılan", f"{used_count:,}".replace(",", "."))
    metric_cols[2].metric("Ağırlıklı medyan", format_try(median_price))
    metric_cols[3].metric("Güven", confidence)
    metric_cols[4].metric("Uç değer", str(outlier_count))

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.subheader("Fiyat Dağılımı")
        render_price_distribution(market_df, {"median": median_price})
    with right:
        st.subheader("Piyasa Göstergesi")
        render_market_gauge(
            {
                "median": median_price,
                "q1": range_low,
                "q3": range_high,
                "min": summary["min"],
                "max": summary["max"],
            }
        )

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Yıl ve Fiyat İlişkisi")
        render_price_by_year(market_df)
    with right:
        st.subheader("Kilometre ve Fiyat İlişkisi")
        render_price_by_mileage(market_df)

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Şehir Yoğunluğu")
        city_counts = market_df["city"].fillna("Bilinmiyor").value_counts().head(10).reset_index()
        city_counts.columns = ["city", "count"]
        fig = px.bar(
            city_counts,
            x="count",
            y="city",
            orientation="h",
            color_discrete_sequence=["#b42318"],
            labels={"count": "İlan sayısı", "city": "Şehir"},
        )
        fig.update_layout(
            height=330,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="#161d27",
            plot_bgcolor="#161d27",
            font=dict(color="#f4f7fb"),
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig, width="stretch")
    with right:
        st.subheader("Eklenme Tarihine Göre Fiyat Trendi")
        render_listing_date_price_trend(market_df)

    st.subheader("Eşleşen İlanlar")
    st.caption(
        "Fiyat aralığı en yakın ilanlardan hesaplanır; bu tabloda filtreye uyan tüm kayıtlar gösterilir."
    )
    listing_table = filtered[
        ["title", "brand", "series", "year", "mileage_km", "city", "price", "listing_url"]
    ].sort_values("price")
    listing_table = listing_table.rename(
        columns={
            "title": "İlan",
            "brand": "Marka",
            "series": "Seri",
            "year": "Yıl",
            "mileage_km": "Kilometre",
            "city": "Şehir",
            "price": "Fiyat",
            "listing_url": "Bağlantı",
        }
    )
    st.dataframe(
        listing_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Fiyat": st.column_config.NumberColumn(format="%d TL"),
            "Kilometre": st.column_config.NumberColumn(format="%d km"),
            "Bağlantı": st.column_config.LinkColumn(display_text="İlana git"),
        },
    )


if __name__ == "__main__":
    main()
