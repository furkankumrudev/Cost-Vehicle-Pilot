# Data

Bu klasör ArabamFiyat.com'un referans ve yerel çalışma verilerini tutar.

## Klasörler

```text
data/
  reference/
    vehicle_catalog.json
  runtime/
    vehicle_listings.sqlite3
```

## Reference Data

`data/reference/vehicle_catalog.json`, arayüzdeki marka, seri ve model/paket seçimlerini besleyen katalog dosyasıdır.

Bu dosya Git'e dahildir; çünkü uygulamanın dropdown seçenekleri için sabit referans veri gibi kullanılır.

## Runtime Data

`data/runtime/vehicle_listings.sqlite3`, scraper tarafından toplanan güncel ilanların tutulduğu yerel SQLite veritabanıdır.

Bu klasör Git'e dahil edilmez. İçinde SQLite veritabanı, checkpoint dosyaları, debug HTML çıktıları ve tarayıcı profili gibi makineye özel çalışma dosyaları bulunur.

## Veri Akışı

```text
Scraper
  -> yeni ilanları vehicle_listings tablosuna ekler
  -> cleaning hattı vehicle_listings_clean tablosunu üretir
  -> Streamlit arayüzü temiz tablodan piyasa analizini gösterir
```

## Not

Projenin ana yaklaşımı hazır statik fiyat dataset'i yerine güncel ilan verisiyle piyasa aralığı üretmektir.
