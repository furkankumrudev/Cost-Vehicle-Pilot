# Sprint 1 - Veri ve Analiz Temeli

## Sprint Hedefi

Guncel ilan verisini toplayan, normalize eden ve benzer ilanlardan anlamli bir piyasa araligi ureten ilk calisan MVP'yi olusturmak.

## Tamamlanan Urun Ciktilari

- Sahibinden sonuc sayfalarindan ilan kaydi icin scraper modulleri.
- SQLite ham tablo, temiz analiz tablosu ve veri cleaning hatti.
- Marka/seri/model katalog yapisi.
- Benzerlik skoru, aykiri fiyat temizleme ve guven seviyesi veren piyasa motoru.
- Streamlit ile ilk yerel analiz arayuzu.

## Sprint Review Icin Kanit

- Kod: `src/ingestion/`, `src/maintenance/`, `src/analysis/market_engine.py`, `src/app.py`
- Veri sozlugu: `docs/data-dictionary.md`
- Urun vizyonu: `docs/product-vision.md`

## Daily Scrum ve Board Kaniti

Gercek daily Scrum kayitlari ve board ekran goruntuleri `evidence/` klasorune eklenmelidir. Bu repoda uydurma toplantı kaydi tutulmaz.

## Retrospective Baslangic Notu

- Scraper calisma hizi ve erisim korumalari risk olarak goruldu.
- Ham veri ile temiz analiz verisinin ayrilmasi karari alindi.
- Sonraki sprintte kullanici arayuzu ve API ayrimi onceliklendirildi.
