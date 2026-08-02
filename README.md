# ArabamFiyat.com

ArabamFiyat.com, ikinci el araç alıcı ve satıcılarının benzer araçlardaki fiyat belirsizliğini azaltmak için geliştirilmiş veri destekli bir karar destek uygulamasıdır.

Kullanıcı marka, seri, model, yıl ve kilometre bilgisini girer. Uygulama yerel SQLite veritabanındaki temizlenmiş güncel ilanları karşılaştırır; piyasa değeri, önerilen fiyat aralığı, fiyat trendi ve yıl/kilometre ilişkisini gösterir. Boya ve değişen bilgisi varsa, ML modeli bu durumun göreli etkisini güncel piyasa değerine uygular.

> Bu ürün bir ekspertiz ya da kesin satış fiyatı hizmeti değildir. Sonuçlar, mevcut ilan verisinden üretilen karar destek tahminleridir.

## Demo

[2 dakikalık ürün demosunu YouTube'da izle](https://youtu.be/CIdeayz5XvY)

## Takım

| Takım adı | Üye | Roller |
| --- | --- | --- |
| ArabamFiyat.com | [Furkan Kumru](https://github.com/furkankumrudev) | Product Owner, Scrum Master, Developer |

Bu proje bireysel olarak geliştirildi; ürün planlama, veri/ML geliştirme, backend, frontend ve test sorumlulukları aynı geliştirici tarafından yürütüldü.

## Ana Teknolojiler

```text
React + TypeScript + Vite  ->  FastAPI  ->  SQLite
                                      ->  Piyasa analiz motoru
                                      ->  CatBoost kondisyon etkisi modeli
```

- Ana kullanıcı arayüzü: `web/`
- API: `src/api/`
- Piyasa motoru: `src/analysis/market_engine.py`
- Veri temizleme: `src/maintenance/clean_vehicle_data.py`
- Model eğitimi ve çıkarımı: `src/ml/`

Final ürün arayüzü React uygulamasıdır; demo ve geliştirme akışı `web/` klasöründen yürütülür.

## Hızlı Başlangıç

### Gereksinimler

- Python 3.11 veya üstü
- Node.js 20 veya üstü
- npm
- Analiz için izinli ve yerel bir SQLite ilan veritabanı

### Kurulum

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
cd web
npm ci
cd ..
```

`.env` dosyasında `SQLITE_DB_PATH` ile analiz veritabanının yolunu tanımlayabilirsin. Varsayılan yol:

```text
data/runtime/vehicle_listings.sqlite3
```

Veritabanı ve model artefaktları Git'e dahil edilmez. Uygulama bu veri bulunmadığında açık bir durum mesajı döndürür; sahte piyasa sonucu üretmez.

### Docker ile demo (önerilen)

Docker Desktop açıksa uygulamanın tamamını tek komutla başlat:

```bat
docker compose up --build
```

Ardından uygulamayı `http://localhost:8080` adresinden aç. Bu akışta React arayüzü ve FastAPI aynı adres üzerinden birlikte çalışır.

### Geliştirme ortamı

İki ayrı terminal aç:

```bat
scripts\run_api.bat
```

```bat
scripts\run_web_app.bat
```

Adresler:

```text
Web:      http://127.0.0.1:5173
API:      http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs
```

## Doğrulama

Backend testlerini ve React production build'ini tek komutla çalıştır:

```bat
scripts\verify_project.bat
```

Manuel olarak:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
cd web
npm run build
```

## ML Modeli

Model, güncel TL fiyatını doğrudan tahmin etmek için kullanılmaz. Eski eğitim verisinden boya ve değişen durumunun göreli etkisini öğrenir; bu katsayı güncel ilanlardan hesaplanan piyasa değerine uygulanır.

Eğitim ve metrikler için [model kartına](docs/model-card.md), sistemin bileşenleri için [mimari dokümanına](docs/architecture.md) bak.

Yerel Kaggle CSV dosyası proje kökünde `car_price_prediction.csv` adıyla varsa modeli yeniden eğitmek için:

```bat
scripts\train_price_model.bat
```

## Veri İlkeleri

- Uygulama analizde temizlenmiş ilan tablosunu tercih eder; temiz tablo yoksa ham tabloya güvenli biçimde geri döner.
- Tarihsel trendler yalnızca gerçekten kaydedilmiş tarih veya snapshot verisinden üretilir.
- Geçmiş veri yetersizse uygulama sahte değişim yüzdesi ya da düz çizgi göstermez.
- Veri alma katmanı, izinli veri kaynakları, resmi API'ler veya partner akışlarıyla değiştirilebilecek şekilde ayrıştırılmıştır.

## Dokümantasyon

- [Ürün vizyonu](docs/product-vision.md)
- [Hedef kitle](docs/target-audience.md)
- [Pazar araştırması](docs/market-research.md)
- [Veri sözlüğü](docs/data-dictionary.md)
- [Model kartı](docs/model-card.md)
- [Mimari](docs/architecture.md)
- [Docker ile çalıştırma](docs/deployment.md)
- [Bootcamp teslim kontrol listesi](docs/bootcamp-delivery.md)
- [Sprint ve backlog belgeleri](ProjectManagement/README.md)

## Lisans

Bu repo [MIT License](LICENSE) altında lisanslanmıştır.
