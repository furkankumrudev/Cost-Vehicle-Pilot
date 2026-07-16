# Cost Vehicle Pilot

Cost Vehicle Pilot, ikinci el araç ilanlarından güncel piyasa fiyat aralığı çıkaran yerel bir MVP uygulamasıdır.

Kullanıcı araç özelliklerini seçer; uygulama SQLite veritabanındaki temizlenmiş Sahibinden ilanlarından benzer kayıtları bulur ve fiyat dağılımı, önerilen fiyat bandı, şehir dağılımı, kilometre/yıl ilişkisi ve benzer ilan listesini gösterir.

## Mevcut Durum

- Streamlit tabanlı analiz arayüzü
- Sahibinden ilanlarını SQLite'a kaydeden scraper hattı
- Ham veriden temiz analiz tablosu üreten data cleaning hattı
- Katalog tabanlı marka, seri/model ve paket seçimleri
- Günlük yeni ilan çekme ve katalog kapsama kontrolü

## Çalıştırma

Windows üzerinde:

```bat
scripts\run_app.bat
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

Bu dosya Git'e dahil edilmez. Veritabanındaki ana tablolar:

```text
vehicle_listings           Ham scraper verisi
vehicle_listings_clean     Analizde kullanılan temiz veri
vehicle_listings_rejected  Temizlikte dışlanan kayıtlar ve nedenleri
```

Uygulama `vehicle_listings_clean` tablosu varsa onu kullanır. Temiz tablo yoksa ham tabloya geri düşer.

## Günlük Veri Güncelleme

Son eklenen ilanları fiyat bantlarına bölerek çekmek için:

```bat
scripts\run_recent_listings.bat --days 1 --max-pages 0 --page-size 50 --delay-min 8 --delay-max 14 --manual-wait-seconds 180 --max-old-pages 5 --max-stale-pages 8 --max-repeated-pages 5 --stop-on-access --checkpoint-path data\runtime\recent_daily_checkpoint.json
```

Ardından temiz analiz tablosunu güncelle:

```bat
scripts\clean_vehicle_data.bat
```

Tek komutluk günlük akış için:

```bat
scripts\run_daily_update.bat
```

## Veri Temizleme

Ham veriden temiz analiz tablosunu tekrar üretmek için:

```bat
scripts\clean_vehicle_data.bat
```

Temizlik hattı:

- Eksik ya da mantıksız fiyatları dışlar.
- 1980 öncesi ve 2026 sonrası model yıllarını dışlar.
- 700.000 km üstünü dışlar.
- Marka/seri/model alanlarını standartlaştırır.
- Şehir/ilçe alanlarını normalize eder.
- Tekrarlayan ilanları temizler.
- Pasif işaretlenmiş ilanları analiz dışı bırakır.

## Kapsama Kontrolü

Arayüzdeki katalog ile temiz veritabanını karşılaştırmak için:

```bat
scripts\audit_catalog_coverage.bat
```

Az ya da boş kalan marka-seri gruplarını hedefli çekmek için:

```bat
scripts\run_series_gaps.bat --skip-history --series-limit 10 --pages-per-series 0 --delay-min 10 --delay-max 16 --delay-between-series 18 --manual-wait-seconds 180 --stop-on-access
```

Bu komut her çalışmada daha önce denenmiş hedefleri atlayabilir ve yeni bulunan ilanları ham tabloya ekler. Çekim bittikten sonra yine `scripts\clean_vehicle_data.bat` çalıştırılmalıdır.

## Yardımcı Bakım

Kaldırılmış ilanları URL üzerinden kontrol etmek için:

```bat
scripts\check_removed_listings.bat --limit 100 --delay-min 2 --delay-max 5 --manual-wait-seconds 120 --stop-on-access
```

Bu komut yayından kalkmış görünen ilanları ham tabloda pasif işaretler. Ardından temiz tabloyu yenilemek gerekir.

## Proje Yapısı

```text
Cost-Vehicle-Pilot/
  README.md
  requirements.txt
  scripts/
    run_app.bat
    run_daily_update.bat
    run_recent_listings.bat
    run_series_gaps.bat
    audit_catalog_coverage.bat
    clean_vehicle_data.bat
    check_removed_listings.bat
  src/
    app.py
    ingestion/
      category_page_scraper.py
      recent_listing_scraper.py
      series_gap_scraper.py
      sahibinden_scraper.py
      schema.py
      storage.py
    maintenance/
      audit_catalog_coverage.py
      clean_vehicle_data.py
      check_removed_listings.py
  data/
    reference/
      vehicle_catalog.json
    runtime/
      vehicle_listings.sqlite3
```

`data/runtime/` Git'e dahil edilmez; SQLite veritabanı ve scraper checkpoint dosyaları yerel çalışma verisidir.

## Not

Bu proje yerel geliştirme ve MVP amaçlıdır. Scraping işlemleri kontrollü yapılmalı, kaynak sitenin kullanım koşulları ve güvenlik mekanizmaları dikkate alınmalıdır.
