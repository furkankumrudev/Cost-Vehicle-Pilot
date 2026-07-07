# Data Dictionary

## Vehicle Catalog

Source file: `data/reference/vehicle_catalog.json`

| Field | Description |
| --- | --- |
| source | Katalog dosyasının üretildiği kaynak açıklaması |
| brand_count | Katalogdaki marka sayısı |
| series_count | Katalogdaki seri sayısı |
| model_count | Katalogdaki model/paket sayısı |
| brands | Marka listesi |
| brands[].name | Marka adı |
| brands[].series | Markaya ait seri listesi |
| brands[].series[].name | Seri adı |
| brands[].series[].models | Seri altındaki model/paket listesi |

## Runtime Listing Database

Source file: `data/runtime/vehicle_listings.sqlite3`

Table: `vehicle_listings`

| Column | Description |
| --- | --- |
| id | Lokal kayıt kimliği |
| source | Veri kaynağı |
| source_listing_id | Kaynak sitedeki ilan kimliği |
| title | İlan başlığı |
| brand | Marka |
| series | Seri |
| model | Model veya paket bilgisi |
| year | Model yılı |
| mileage_km | Kilometre |
| transmission | Vites tipi |
| fuel_type | Yakıt tipi |
| body_type | Kasa tipi |
| color | Renk |
| engine | Motor bilgisi |
| city | Şehir |
| district | İlçe |
| seller_type | Satıcı tipi |
| price | İlan fiyatı |
| currency | Para birimi |
| listing_date | İlan tarihi |
| listing_url | İlan bağlantısı |
| image_url | Görsel bağlantısı |
| scraped_at | Verinin toplandığı zaman |

## Analysis Output

Streamlit arayüzü bu kayıtlardan şu değerleri üretir:

- benzer ilan sayısı
- minimum fiyat
- maksimum fiyat
- ortalama fiyat
- medyan fiyat
- 25. yüzdelik fiyat
- 75. yüzdelik fiyat
- önerilen piyasa fiyat aralığı
