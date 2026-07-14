# Cost Vehicle Pilot

Cost Vehicle Pilot, ikinci el araçların piyasa fiyat aralığını güncel ilan verisiyle analiz eden yerel bir MVP uygulamasıdır.

Kullanıcı araç özelliklerini seçer; uygulama SQLite veritabanındaki temizlenmiş Sahibinden ilanlarından benzer kayıtları bulur ve fiyat dağılımı, medyan değer, önerilen fiyat bandı ve benzer ilan listesini gösterir.

## Mevcut Durum

- Streamlit tabanlı analiz arayüzü
- Sahibinden ilanlarını SQLite'a kaydeden scraper modülleri
- Ham veriden temiz analiz tablosu oluşturan data cleaning hattı
- Marka, seri/model, yıl, kilometre, şehir ve fiyat temelli piyasa analizi

## Çalıştırma

Windows üzerinde:

```bat
scripts\run_app.bat
```

Alternatif:

```bash
streamlit run src/app.py
```

Varsayılan adres:

```text
http://127.0.0.1:8501
```

## Veri

Ana veritabanı:

```text
data/runtime/vehicle_listings.sqlite3
```

Bu dosya Git'e dahil edilmez. Veritabanında üç ana tablo bulunur:

```text
vehicle_listings           Ham scraper verisi
vehicle_listings_clean     Analizde kullanılan temiz veri
vehicle_listings_rejected  Temizlikte dışlanan kayıtlar ve nedenleri
```

Uygulama `vehicle_listings_clean` tablosu varsa otomatik olarak onu kullanır. Temiz tablo yoksa ham tabloya geri düşer.

## Veri Temizleme

Ham veriden temiz analiz tablosunu tekrar üretmek için:

```bat
scripts\clean_vehicle_data.bat
```

Varsayılan temizlik kuralları:

- Fiyatı eksik veya 50.000 TL altı olan kayıtları dışlar.
- 150.000.000 TL üstünü dışlar.
- 1980 öncesi ve 2026 sonrası model yıllarını dışlar.
- 700.000 km üstünü dışlar.
- Marka kolonuna kaçan seri/model değerlerini ilan URL'sinden düzeltmeye çalışır.
- Bilinmeyen marka kayıtlarını `vehicle_listings_rejected` tablosuna ayırır.

Kaldırılmış ilanları kontrol etmek için:

```bat
scripts\check_removed_listings.bat --limit 100 --delay-min 2 --delay-max 5 --manual-wait-seconds 120 --stop-on-access
```

Bu komut ilan URL'lerini tek tek açar. Yayından kaldırılmış görünen ilanları ham tabloda `is_active = 0` olarak işaretler. Ardından temiz tabloyu yenilemek için:

```bat
scripts\clean_vehicle_data.bat
```

`vehicle_listings_clean` tablosu pasif ilanları analize dahil etmez.

## Scraper Komutları

Marka marka toplama:

```bat
scripts\run_brand_segments.bat --pages-per-brand 0 --page-size 50 --delay-min 2 --delay-max 5 --delay-between-brands 8 --manual-wait-seconds 120 --max-empty-pages 2 --max-low-change-pages 8 --max-repeated-pages 1 --stop-on-access
```

Şehir şehir toplama:

```bat
scripts\run_city_segments.bat --pages-per-city 0 --page-size 50 --delay-min 6 --delay-max 12
```

İlçe ilçe toplama:

```bat
scripts\run_district_segments.bat --city istanbul --pages-per-district 0 --page-size 50 --delay-min 8 --delay-max 18 --manual-wait-seconds 180 --stop-on-access
```

Yeni/taze ilanları fiyat bantlarına bölerek toplama:

```bat
scripts\run_recent_listings.bat --days 3650 --max-pages 0 --page-size 50 --price-bands 0-300000,300001-600000,600001-900000,900001-1200000,1200001-1600000,1600001-2200000,2200001-3000000,3000001-5000000,5000001+ --delay-min 1 --delay-max 3 --manual-wait-seconds 90 --max-old-pages 0 --max-stale-pages 0 --max-repeated-pages 1 --stop-on-access
```

Vites filtresiyle şehir bazlı toplama:

```bat
scripts\run_city_transmission_segments.bat --city ankara --transmissions manuel,otomatik --pages-per-transmission 0 --page-size 50 --delay-min 3 --delay-max 7 --manual-wait-seconds 90 --stop-on-access
```

Scraper sırasında Sahibinden güvenlik ekranı gelirse açılan tarayıcıda işlemi elle tamamlamak gerekir.

## Proje Yapısı

```text
Cost-Vehicle-Pilot/
  README.md
  requirements.txt
  scripts/
    run_app.bat
    clean_vehicle_data.bat
    check_removed_listings.bat
    run_brand_segments.bat
    run_city_segments.bat
    run_district_segments.bat
    run_recent_listings.bat
    run_city_transmission_segments.bat
  src/
    app.py
    ingestion/
      brand_segment_scraper.py
      category_page_scraper.py
      city_segment_scraper.py
      city_transmission_segment_scraper.py
      district_segment_scraper.py
      recent_listing_scraper.py
      sahibinden_scraper.py
      schema.py
      storage.py
    maintenance/
      clean_vehicle_data.py
  data/
    reference/
      vehicle_catalog.json
    runtime/
      vehicle_listings.sqlite3
```

## Not

Bu proje yerel geliştirme ve MVP amaçlıdır. Scraping işlemleri kontrollü yapılmalı, kaynak sitenin kullanım koşulları ve güvenlik mekanizmaları dikkate alınmalıdır.
