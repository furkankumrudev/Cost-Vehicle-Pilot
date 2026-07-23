# Sprint 2 - API ve Web Uygulamasi

## Sprint Hedefi

Gercek SQLite verisini kullanan FastAPI katmanini ve profesyonel React arayuzunu, eski Streamlit arayuzunu bozmadan eklemek.

## Tamamlanan Urun Ciktilari

- FastAPI katalog, piyasa, trend, benzer ilan ve degerleme endpointleri.
- React/Vite ile piyasa trendleri ve arac degerleme sayfalari.
- Gercek ilan tarihinden medyan/ortalama fiyat trendi.
- Gelecekteki gercek fiyat degisimi icin gunluk snapshot tasarimi.
- Mobil/tablet/masaustu responsive kontrolu.

## Sprint Review Icin Kanit

- API: `src/api/`
- Web uygulamasi: `web/`
- Testler: `tests/test_api_services.py`
- Calistirma rehberi: `README.md`

## Daily Scrum ve Board Kaniti

Gercek board ekran goruntuleri, commit baglantilari ve karar notlari `evidence/` klasorune eklenmelidir.

## Retrospective Baslangic Notu

- Gercek veri olmayan alanlarda sahte grafik veya yuzde gosterilmemesi urun ilkesi olarak benimsendi.
- Streamlit legacy/internal arayuz, React ise ana urun arayuzu olarak ayrildi.
- Sonraki sprintte ML modeli, kalite metrikleri ve deploy onceliklendirildi.
