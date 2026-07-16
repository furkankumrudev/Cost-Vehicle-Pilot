"""Streamlit interface for Cost Vehicle Pilot."""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "runtime" / "vehicle_listings.sqlite3"
CATALOG_PATH = PROJECT_ROOT / "data" / "reference" / "vehicle_catalog.json"
ALL_OPTION = "Tümü"
MIN_SAMPLE_SIZE = 8

BRAND_ALIASES = {
    "mercedesbenz": "Mercedes-Benz",
    "tofa": "Tofaş",
    "tofas": "Tofaş",
    "tofat": "Tofaş",
}


st.set_page_config(
    page_title="Cost Vehicle Pilot",
    page_icon="CVP",
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
        border-bottom: 1px solid var(--cvp-line);
        padding: 0 0 1rem 0;
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
    return df[series_mask | title_mask]


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


def render_price_percentile_tool(df: pd.DataFrame, summary: dict[str, float | int]) -> None:
    """Kullanıcının kendi aracının/ilanının fiyatını girmesini sağlar ve bunu
    filtrelenmiş benzer ilanların fiyat dağılımıyla kıyaslar."""
    prices = df["price"].dropna()
    if prices.empty:
        st.info("Kıyaslama için yeterli veri yok.")
        return

    default_value = int(summary.get("median", 0))
    user_price = st.number_input(
        "Aracınızın fiyatını girin (TL)",
        min_value=0,
        value=default_value,
        step=10000,
        help="Kendi aracınızın (ya da incelediğiniz ilanın) fiyatını girin; "
             "bu, soldaki filtrelerle eşleşen ilanlarla karşılaştırılır.",
    )

    if user_price <= 0:
        st.caption("Karşılaştırma için bir fiyat girin.")
        return

    percentile = float((prices < user_price).mean() * 100)
    cheaper_count = int((prices < user_price).sum())

    st.metric(
        "Piyasa yüzdelik dilimi",
        f"%{percentile:.0f}",
        help=f"Benzer {len(prices)} ilanın %{percentile:.0f}'i bu fiyattan daha ucuz.",
    )
    st.caption(
        f"Girdiğiniz {format_try(user_price)} fiyatı, {len(prices)} benzer ilanın "
        f"{cheaper_count} tanesinden daha pahalı (yani ilanların %{percentile:.0f}'inden pahalı, "
        f"%{100 - percentile:.0f}'inden ucuz)."
    )

    q1, q3, median = summary["q1"], summary["q3"], summary["median"]
    if user_price < q1:
        st.success(
            f"Bu fiyat, önerilen piyasa aralığının ({format_try(q1)} - {format_try(q3)}) ALTINDA. "
            "Alıcı için avantajlı olabilir, ancak bu denli düşükse aracın durumunu/kilometresini "
            "tekrar kontrol etmekte fayda var."
        )
    elif user_price > q3:
        st.warning(
            f"Bu fiyat, önerilen piyasa aralığının ({format_try(q1)} - {format_try(q3)}) ÜZERİNDE. "
            "Satıcı için avantajlı olabilir, alıcı için pazarlık payı olabilir."
        )
    else:
        st.info(
            f"Bu fiyat, önerilen piyasa aralığı ({format_try(q1)} - {format_try(q3)}) İÇİNDE — "
            f"medyana ({format_try(median)}) göre gayet makul."
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
            <h1 class="cvp-title">Cost Vehicle Pilot</h1>
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
    summary = price_summary(filtered)

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

    if not summary or len(filtered) < MIN_SAMPLE_SIZE:
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

    range_low = summary["q1"]
    range_high = summary["q3"]

    st.markdown(
        f"""
        <div class="cvp-panel">
            <div class="cvp-kicker">Önerilen piyasa aralığı</div>
            <div class="cvp-range">{format_try(range_low)} - {format_try(range_high)}</div>
            <div class="cvp-copy">
                {summary["count"]} benzer ilanın fiyat dağılımına göre medyan piyasa değeri
                {format_try(summary["median"])}.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(5)
    metric_cols[0].metric("Benzer ilan", f"{summary['count']:,}".replace(",", "."))
    metric_cols[1].metric("En düşük", format_try(summary["min"]))
    metric_cols[2].metric("Medyan", format_try(summary["median"]))
    metric_cols[3].metric("Ortalama", format_try(summary["mean"]))
    metric_cols[4].metric("En yüksek", format_try(summary["max"]))

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.subheader("Fiyat Dağılımı")
        render_price_distribution(filtered, summary)
    with right:
        st.subheader("Piyasa Göstergesi")
        render_market_gauge(summary)

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Yıl ve Fiyat İlişkisi")
        render_price_by_year(filtered)
    with right:
        st.subheader("Kilometre ve Fiyat İlişkisi")
        render_price_by_mileage(filtered)

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Şehir Yoğunluğu")
        city_counts = filtered["city"].fillna("Bilinmiyor").value_counts().head(10).reset_index()
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
        st.subheader("Aracınızın Piyasadaki Yeri")
        render_price_percentile_tool(filtered, summary)

    st.subheader("Benzer İlanlar")
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
