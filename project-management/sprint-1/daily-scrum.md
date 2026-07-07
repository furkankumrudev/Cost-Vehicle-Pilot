# Daily Scrum - Sprint 1

## 04.07.2026

### Dün Ne Yapıldı?

- Bootcamp proje gereksinimleri incelendi.
- Proje fikri ikinci el araç adil fiyat tahmini olarak belirlendi.
- Ürün adı Cost Vehicle Pilot olarak seçildi.

### Bugün Ne Yapılacak?

- GitHub repo yapısı hazırlanacak.
- README ve proje dokümantasyonu oluşturulacak.
- Product backlog ilk versiyonu yazılacak.

### Engel Var mı?

- Şu an için bilinen bir blocker yok.

## 05.07.2026

### Dün Ne Yapıldı?

- GitHub repo yapısı oluşturuldu.
- README, ürün vizyonu, hedef kitle ve sprint dokümanları hazırlandı.

### Bugün Ne Yapıldı?

- Public ikinci el araç fiyat veri seti seçildi.
- Ham veri `data/raw/used_car_prices.csv` dosyasına eklendi.
- Veri temizleme script'i `src/data_preprocessing.py` olarak oluşturuldu.
- Temizlenmiş veri `data/processed/used_car_prices_clean.csv` olarak üretildi.
- Veri stratejisi ve data dictionary dokümanları hazırlandı.

### Engel Var mı?

- Türkiye odaklı ve güncel veri kaynağı henüz bulunmadı. İlk MVP için public dataset kullanılacak; mimari sonradan API veya Türkiye odaklı veriyle değiştirilebilir şekilde hazırlanacak.

## 07.07.2026

### Dün Ne Yapıldı?

- Bootcamp kriterleri tekrar incelendi.
- Statik veri seti yaklaşımının sürdürülebilirlik açısından sınırlı kalabileceği değerlendirildi.

### Bugün Ne Yapıldı?

- Sahibinden ilanlarından güncel veri toplayabilecek scraper mimarisi araştırıldı.
- Projeye `src/ingestion` altında ilk scraper veri toplama katmanı eklendi.
- SQLite tabanlı ilan kayıt şeması oluşturuldu.
- Scraper stratejisi `docs/scraper-strategy.md` dosyasında belgelendi.

### Engel Var mı?

- Scraping işlemleri site kuralları, erişim engelleri ve sayfa yapısı değişiklikleri nedeniyle risk taşıyor. Bu nedenle MVP'de veri toplama katmanı kontrollü ve sınırlı kullanılacak; mimari izinli veri kaynaklarına uyarlanabilir şekilde geliştirilecek.