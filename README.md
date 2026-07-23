# ArabamFiyat.com

## Yeni Web Uygulamasi (FastAPI + React)

Proje iki arayuzu birlikte korur:

- `src/app.py`: mevcut Streamlit analizi; yerel/legacy arayuz olarak kullanilabilir.
- `web/`: yeni, gercek SQLite verisine baglanan React + TypeScript web uygulamasi.

Yeni mimari:

```text
React + Vite (web/)  ->  FastAPI (src/api/)  ->  SQLite
                                        ->  src/analysis/market_engine.py
```

### Web uygulamasini calistirma

Ilk kurulumda Python paketlerini ve web paketlerini kurun:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
cd web
npm install
cd ..
```

Iki ayri terminal acin:

```bat
scripts\run_api.bat
scripts\run_web_app.bat
```

Adresler:

```text
Web:      http://127.0.0.1:5173
API:      http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs
```

Yeni web uygulamasi, `vehicle_listings_clean` tablosunu tercih eder; tablo yoksa `vehicle_listings` ham tablosunu kullanir. `data/runtime/vehicle_listings.sqlite3` bulunmuyorsa API guvenli bir "veritabani henuz bulunamadi" durumu dondurur.

### Gercek tarihsel fiyat takibi

Trend grafigi, yalnizca ilan kayitlarindaki gercek ilan tarihlerini kullanir ve "Ilan tarihine gore medyan fiyat" olarak etiketlenir. 30/90 gun ve yillik degisim oranlari, ancak farkli gunlerde kaydedilmis gercek snapshotlar biriktiginde gorunur. Eksik gecmis veri icin sahte oran veya duz cizgi uretilmez.

Gunun piyasa ozetini gelecekteki karsilastirmalar icin kaydetmek uzere, gunluk scraper ve cleaning adimindan sonra su komut calistirilabilir:

```bat
scripts\save_market_snapshot.bat
```

Bu komut `market_price_snapshots` tablosunu gerekirse olusturur ve yalnizca calistirildigi gunun gercek ozetini yazar; gecmisi uydurarak doldurmaz.

### Ekran goruntuleri

`docs/screenshots/` altina web ana sayfa, piyasa trendleri ve arac degerleme ekran goruntuleri eklenebilir.

ArabamFiyat.com, ikinci el araç ilanlarından güncel piyasa fiyat aralığı çıkaran yerel bir MVP uygulamasıdır.

Kullanıcı araç özelliklerini seçer; uygulama SQLite veritabanındaki temizlenmiş Sahibinden ilanlarından benzer kayıtları bulur ve fiyat dağılımı, önerilen fiyat bandı, şehir dağılımı, kilometre/yıl ilişkisi ve benzer ilan listesini gösterir.

## Mevcut Durum

- Streamlit tabanlı analiz arayüzü
- Sahibinden ilanlarını SQLite'a kaydeden scraper hattı
- Ham veriden temiz analiz tablosu üreten data cleaning hattı
- Katalog tabanlı marka, seri/model ve paket seçimleri
- Günlük genel son 24 saat ve temiz iddialı ilan scraper komutları
- Benzerlik skoru, uç fiyat temizleme ve güven seviyesi üreten piyasa analiz motoru

## Kurulum

Windows üzerinde sanal ortam oluşturup bağımlılıkları kurmak için:

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Çalıştırma

Windows üzerinde:

```bat
scripts\run_app.bat
```

Varsayılan adres:

```text
http://127.0.0.1:8501
```

## Web Prototipi

Streamlit disinda daha profesyonel bir web arayuzu prototipi de vardir:

```text
frontend/index.html
```

Dosyayi direkt tarayicida acabilir veya statik server ile calistirabilirsin:

```bat
scripts\run_web_frontend.bat
```

Bu eski statik prototiptir. Ana urun arayuzu `web/` klasorundedir. Varsayilan legacy adres:

```text
http://127.0.0.1:5174
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

Genel son 24 saat ilanlarını dar fiyat bantlarına bölerek çekmek ve ardından temiz tabloyu otomatik yenilemek için:

```bat
scripts\run_daily_update.bat
```

Boyasız/değişensiz filtreli temiz iddialı son 24 saat ilanlarını ayrı toplamak için:

```bat
scripts\run_daily_clean_update.bat
```

İki komut da aynı 37 fiyat bandını kullanır. Genel komut `--filter-segments general`, temiz komut `--filter-segments clean` ile `recent_listing_scraper.py` modülünü çalıştırır. Temiz komutla yakalanan ilanlar `is_clean_claimed = 1`, `paint_status = Boyasız`, `changed_part_status = Değişensiz` ve `damage_status = clean_claimed` olarak işaretlenir.

Daha geniş bir aralık çekmek istersen `run_recent_listings.bat` komutunu `--days N` ile çalıştırıp sonrasında temizlik komutunu elle çalıştırabilirsin:

```bat
scripts\run_recent_listings.bat --days 1 --filter-segments general --max-pages 0 --page-size 50 --delay-min 8 --delay-max 14 --manual-wait-seconds 180 --max-old-pages 5 --max-stale-pages 8 --max-repeated-pages 5 --stop-on-access --checkpoint-path data\runtime\recent_manual_checkpoint.json
scripts\clean_vehicle_data.bat
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
- Başlıkta `boyasız` geçen eski ilanları `is_clean_claimed = 1` olarak işaretler.
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
    run_daily_clean_update.bat
    run_recent_listings.bat
    run_series_gaps.bat
    audit_catalog_coverage.bat
    clean_vehicle_data.bat
    check_removed_listings.bat
  src/
    app.py
    analysis/
      market_engine.py
    ingestion/
      brand_segment_scraper.py
      category_page_scraper.py
      city_segment_scraper.py
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
