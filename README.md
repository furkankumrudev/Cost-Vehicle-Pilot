# Cost Vehicle Pilot

Cost Vehicle Pilot, ikinci el araç almak veya satmak isteyen kullanıcılar için geliştirilmiş güncel piyasa analizi ve fiyat aralığı öneri platformudur.

Kullanıcı araç özelliklerini seçer; sistem benzer ilanları analiz ederek fiyat dağılımını, medyan piyasa değerini ve önerilen fiyat aralığını gösterir.

## Proje Mantığı

Hazır ve eski bir veri setine bağlı kalmak yerine proje, güncel ilan verisiyle çalışabilecek bir veri toplama ve analiz mimarisi üzerine kurulmaktadır.

```text
Araç özellikleri formu
  -> Sahibinden arama sorgusu
  -> güncel ilan verisi toplama
  -> SQLite kayıt katmanı
  -> benzer ilan filtreleme
  -> fiyat dağılımı ve piyasa aralığı
  -> Streamlit dashboard
```

İlk MVP'de odak, kullanıcının seçtiği araç özelliklerine göre benzer ilanların fiyat dağılımını göstermektir.

## Ürün Özellikleri

- Marka, seri ve model/paket seçimi
- Model yılı ve maksimum kilometre filtresi
- Güncel ilan havuzundan benzer araç analizi
- Minimum, maksimum, ortalama ve medyan fiyat
- 25-75 yüzdelik aralığa göre önerilen piyasa fiyat bandı
- Fiyat dağılım grafiği
- Model yılı ve fiyat ilişkisi
- Şehir yoğunluğu grafiği
- Benzer ilan tablosu ve ilan bağlantıları

## Veri Mimarisi

Projede üç ana veri katmanı vardır:

| Katman | Dosya / Konum | Amaç |
| --- | --- | --- |
| Araç katalogu | `data/reference/vehicle_catalog.json` | Marka, seri ve model/paket seçimlerini besler |
| Güncel ilan verisi | `data/runtime/vehicle_listings.sqlite3` | Scraper ile toplanan ilanları lokal SQLite veritabanında tutar |
| Scraper modülü | `src/ingestion/` | Sahibinden arama sonuçlarından normalize ilan verisi toplamayı hedefler |

`data/runtime/` klasörü lokal çalışma verisidir ve Git'e dahil edilmez.

## Arayüzü Çalıştırma

Windows üzerinde:

```bat
scripts\run_app.bat
```

veya:

```bash
streamlit run src/app.py
```

Varsayılan adres:

```text
http://127.0.0.1:8501
```

## Scraper Kullanımı

Kontrollü tek sayfalık örnek:

```bash
python -m src.ingestion.sahibinden_scraper --query "Renault Clio" --year-min 2020 --year-max 2025 --max-pages 1
```

Chrome veya Edge yolu gerekiyorsa:

```bash
python -m src.ingestion.sahibinden_scraper --query "Renault Clio" --max-pages 1 --browser-executable-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

Scraping işlemleri kontrollü, düşük hacimli ve kaynak sitenin kurallarına dikkat edilerek ele alınmalıdır. Uzun vadede aynı mimari resmi API, izinli veri sağlayıcıları veya partner veri akışlarıyla çalışabilecek şekilde tasarlanmıştır.

## Kullanılan Teknolojiler

- Python
- Pandas
- Plotly
- Streamlit
- BeautifulSoup
- Nodriver
- SQLite

## Proje Yapısı

```text
Cost-Vehicle-Pilot/
  README.md
  data/
    reference/
      vehicle_catalog.json
    runtime/                 # lokal çalışma verisi, Git'e girmez
  docs/
    data-dictionary.md
    data-strategy.md
    market-research.md
    product-vision.md
    scraper-strategy.md
    target-audience.md
  project-management/
    sprint-1/
    sprint-2/
    sprint-3/
  scripts/
    run_app.bat
  src/
    app.py
    ingestion/
      sahibinden_scraper.py
      schema.py
      storage.py
```

## Bootcamp Değeri

Bu proje yalnızca statik bir CSV analizi değildir. Ürün, kullanıcının seçtiği araç özelliklerine göre güncel ilan verisi toplayabilecek, bu veriyi analiz edebilecek ve anlaşılır bir dashboard üzerinden fiyat aralığı sunabilecek şekilde tasarlanmaktadır.

## Durum

İlk arayüz MVP'si hazırlanmıştır. Güncel ilanlar SQLite veritabanına yazılabilmekte ve Streamlit dashboard üzerinde fiyat dağılımı olarak gösterilebilmektedir.
