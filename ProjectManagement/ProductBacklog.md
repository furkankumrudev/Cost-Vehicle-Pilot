# Product Backlog

Durumlar proje ilerledikce gercek sprint kararlarina gore guncellenir.

| ID | User story | Oncelik | Durum | Kabul kriteri |
| --- | --- | --- | --- | --- |
| AF-01 | Kullanici olarak marka, seri ve model secebilmeliyim. | Must | Done | Secimler katalog ve veritabanindan gelir. |
| AF-02 | Kullanici olarak yil ve kilometre ile analizi daraltabilmeliyim. | Must | Done | Filtreler API sorgusuna yansir. |
| AF-03 | Kullanici olarak benzer ilanlardan fiyat araligi gorebilmeliyim. | Must | Done | Aykiri fiyatlar disarida birakilir, guven seviyesi gosterilir. |
| AF-04 | Kullanici olarak piyasa trendini gercek ilan tarihlerinden gorebilmeliyim. | Must | Done | Grafik sahte tarihsel veri uretmez. |
| AF-05 | Sistem olarak yeni ilanlari temizleyip analiz tablosuna aktarmaliyim. | Must | Done | Scraper sonrasi cleaning hatti calisir. |
| AF-06 | Kullanici olarak aracimin tahmini piyasa degerini gorebilmeliyim. | Must | Done | FastAPI mevcut piyasa motorunu kullanir. |
| AF-07 | Sistem olarak gunluk piyasa ozetlerini saklamaliyim. | Should | In progress | Tekrarlayan gun kaydi olusmaz. |
| AF-08 | Kullanici olarak yeterli gecmis veri yoksa bunu acikca gormeliyim. | Must | Done | 30/90/yillik alanlarda sahte yuzde gosterilmez. |
| AF-09 | Kullanici olarak ML tabanli fiyat tahmini ile piyasa tahminini karsilastirabilmeliyim. | Must | Planned | Model metrikleri ve tahmin kaynagi gorunur. |
| AF-10 | Gelistirici olarak modeli tekrar egitip metriklerini kaydedebilmeliyim. | Should | Planned | Train/test ayrimi ve MAE/RMSE raporu bulunur. |
| AF-11 | Kullanici olarak urunu mobil ekranda kullanabilmeliyim. | Should | Done | 360px gorunumde yatay tasma olmaz. |
| AF-12 | Juri olarak urunu yerelde veya deploy edilmis ortamda calistirabilmeliyim. | Must | Planned | Kurulum/deploy dokumani ve calisan demo bulunur. |
