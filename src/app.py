"""Streamlit interface for Cost Vehicle Pilot."""

from __future__ import annotations

import sqlite3
import json
from pathlib import Path

import pandas as pd
import plotly.express as px # type: ignore
import plotly.graph_objects as go # type: ignore
import streamlit as st

DB_PATH = Path("data") / "runtime" / "vehicle_listings.sqlite3"
CATALOG_PATH = Path("data") / "reference" / "vehicle_catalog.json"
MIN_SAMPLE_SIZE = 8


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
def load_vehicle_catalog(path: str) -> dict[str, object]:
    catalog_path = Path(path)
    if not catalog_path.exists():
        return {"brands": []}
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def catalog_brand_options(catalog: dict[str, object]) -> list[str]:
    brands = catalog.get("brands", [])
    if not isinstance(brands, list):
        return []
    return [str(item["name"]) for item in brands if isinstance(item, dict) and item.get("name")]


def catalog_series_options(catalog: dict[str, object], brand: str) -> list[str]:
    brands = catalog.get("brands", [])
    if not isinstance(brands, list) or brand == "Tümü":
        return []
    for item in brands:
        if isinstance(item, dict) and item.get("name") == brand:
            series = item.get("series", [])
            if not isinstance(series, list):
                return []
            return [str(series_item["name"]) for series_item in series if series_item.get("name")]
    return []


def catalog_model_options(catalog: dict[str, object], brand: str, series: str) -> list[str]:
    brands = catalog.get("brands", [])
    if not isinstance(brands, list) or brand == "Tümü" or series == "Tümü":
        return []
    for item in brands:
        if not isinstance(item, dict) or item.get("name") != brand:
            continue
        series_items = item.get("series", [])
        if not isinstance(series_items, list):
            return []
        for series_item in series_items:
            if isinstance(series_item, dict) and series_item.get("name") == series:
                models = series_item.get("models", [])
                if not isinstance(models, list):
                    return []
                return [str(model) for model in models if model]
    return []


@st.cache_data(show_spinner=False)
def load_listings(db_path: str) -> pd.DataFrame:
    path = Path(db_path)
    if not path.exists():
        return pd.DataFrame()

    with sqlite3.connect(path) as connection:
        df = pd.read_sql_query(
            """
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
            FROM vehicle_listings
            WHERE price IS NOT NULL
            """,
            connection,
        )

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
    if brand != "Tümü":
        filtered = filtered[filtered["brand"].fillna("").str.casefold() == brand.casefold()]
    if series != "Tümü":
        filtered = filtered[filtered["series"].fillna("").str.casefold() == series.casefold()]
    if model != "Tümü":
        model_mask = filtered["model"].fillna("").str.contains(model, case=False, na=False)
        title_mask = filtered["title"].fillna("").str.contains(model, case=False, na=False)
        filtered = filtered[model_mask | title_mask]
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
    st.plotly_chart(fig, use_container_width=True)


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
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="#161d27",
        plot_bgcolor="#161d27",
        yaxis_title="Fiyat (TL)",
        xaxis_title="Model yılı",
        font=dict(color="#f4f7fb"),
    )
    st.plotly_chart(fig, use_container_width=True)


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
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    df = load_listings(str(DB_PATH))
    catalog = load_vehicle_catalog(str(CATALOG_PATH))

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
        brand_options = ["Tümü"] + (catalog_brands or unique_options(df, "brand"))
        brand = st.selectbox("Marka", brand_options, index=0)

        catalog_series = catalog_series_options(catalog, brand)
        series_source = df if brand == "Tümü" else df[df["brand"].fillna("").str.casefold() == brand.casefold()]
        series_options = ["Tümü"] + (catalog_series or unique_options(series_source, "series"))
        series = st.selectbox("Seri / Model", series_options, index=0)

        catalog_models = catalog_model_options(catalog, brand, series)
        model_options = ["Tümü"] + catalog_models
        selected_model = st.selectbox("Model / Paket", model_options, index=0)

        year_values = df["year"].dropna() if not df.empty else pd.Series(dtype="float64")
        min_year = int(year_values.min()) if not year_values.empty else 2000
        max_year = int(year_values.max()) if not year_values.empty else 2026
        year_range = st.slider("Model yılı", min_year, max_year, (max(min_year, 2015), max_year))

        mileage_values = df["mileage_km"].dropna() if not df.empty else pd.Series(dtype="float64")
        max_mileage = int(max(mileage_values.max(), 100000)) if not mileage_values.empty else 300000
        mileage_max = st.slider("Maksimum kilometre", 0, max_mileage, min(max_mileage, 250000), step=5000)

        st.divider()
        analyze = st.button("Piyasa Analizini Göster", use_container_width=True)
        st.caption(f"Veritabanı: {DB_PATH.as_posix()}")
        if catalog_brands:
            st.caption(
                f"Katalog: {catalog.get('brand_count', len(catalog_brands))} marka, "
                f"{catalog.get('series_count', 0)} seri"
            )

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
                <div class="cvp-range">Araç özelliklerini seç</div>
                <div class="cvp-copy">
                    Analiz başlatıldığında benzer ilanların fiyat yoğunluğu, medyan değeri ve önerilen piyasa aralığı hesaplanır.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Toplam ilan", f"{len(df):,}".replace(",", "."))
        col_b.metric("Marka sayısı", f"{df['brand'].nunique(dropna=True)}")
        col_c.metric("Fiyat kaydı", f"{df['price'].notna().sum():,}".replace(",", "."))
        col_d.metric("Son veri", pd.to_datetime(df["scraped_at"], errors="coerce").max().strftime("%d.%m.%Y"))
        return

    if not summary or len(filtered) < MIN_SAMPLE_SIZE:
        st.warning("Bu filtrelerle yeterli benzer ilan bulunamadı. Filtreleri biraz genişlet.")
        st.metric("Eşleşen ilan", len(filtered))
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
        st.plotly_chart(fig, use_container_width=True)

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
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fiyat": st.column_config.NumberColumn(format="%d TL"),
            "Kilometre": st.column_config.NumberColumn(format="%d km"),
            "Bağlantı": st.column_config.LinkColumn(display_text="İlana git"),
        },
    )


if __name__ == "__main__":
    main()
