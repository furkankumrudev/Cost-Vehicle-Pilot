# Docker ile Çalıştırma

Bu yapı, React arayüzü ve FastAPI servisinin tek bir yerel adres altında çalışmasını sağlar. Web uygulaması `http://localhost:8080` adresinden açılır; `/api` istekleri Nginx üzerinden FastAPI konteynerine yönlendirilir.

## Gereksinimler

- Docker Desktop
- Yerel izinli SQLite veritabanı: `data/runtime/vehicle_listings.sqlite3`
- Opsiyonel kondisyon etkisi modeli: `data/models/kaggle_price_effect/kaggle_price_effect_model.cbm`

Veritabanı konteynere salt okunur kaynak olarak bağlanır ve Git'e eklenmez. Başlangıçta konteynerin geçici çalışma alanına kopyalanır; bu, Windows bind mount'larında SQLite dosya kilitleme sorunlarını önler. Veritabanı yoksa API health kontrolü başarısız olur; bu, sahte piyasa verisiyle açılmaktan daha güvenlidir.

## Çalıştırma

```bat
docker compose up --build
```

Uygulama:

```text
http://localhost:8080
```

API dokümantasyonu:

```text
http://localhost:8080/docs
```

## Canlı Ortama Alma Notu

Canlı ortamda SQLite ve model artefaktı Docker imajına eklenmemelidir. Bunlar kalıcı ve erişimi kontrollü bir volume veya izinli bir veri deposundan bağlanmalıdır. Ortam değişkenleriyle `SQLITE_DB_PATH` ve `CORS_ORIGINS` ayarlanabilir.

## Doğrulama

Docker Desktop kurulu bir ortamda aşağıdaki kontroller yapılmalıdır:

```bat
docker compose config
docker compose up --build
```

Ardından web ekranından araç değerleme akışı ve `http://localhost:8080/api/health` endpointi doğrulanmalıdır.
