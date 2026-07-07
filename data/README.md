# Data

Bu klasör Cost Vehicle Pilot'un referans ve lokal çalışma verilerini tutar.

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

Katalog mevcut Türkçe araç ilan verisinden türetilmiştir ve uygulamanın ilk seçim deneyimini hazır hale getirir.

## Runtime Data

`data/runtime/vehicle_listings.sqlite3`, scraper tarafından toplanan güncel ilanların tutulduğu lokal SQLite veritabanıdır.

Bu klasör Git'e dahil edilmez. Çünkü içerik çalışma ortamına, deneme sorgularına ve canlı veri toplama sürecine göre değişir.

## Veri Akışı

```text
Kullanıcı araç özelliklerini seçer
  -> scraper benzer ilanları toplar
  -> SQLite'a kaydeder
  -> Streamlit arayüzü fiyat dağılımını gösterir
```

## Not

Eski public CSV veri seti proje yönünden çıkarılmıştır. Projenin ana yaklaşımı artık hazır statik dataset yerine dinamik ilan verisiyle piyasa aralığı üretmektir.
