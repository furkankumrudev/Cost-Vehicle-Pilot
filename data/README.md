# Data

Bu klasör ArabamFiyat.com'un referans ve yerel çalışma verilerini tutar.

## Klasörler

```text
data/
  reference/
    vehicle_catalog.json
  runtime/
    vehicle_listings.sqlite3
```

## Reference Data

`data/reference/vehicle_catalog.json`, arayüzdeki marka, seri ve model/paket seçimlerini besleyen katalog dosyasıdır.

Bu dosya Git'e dahildir; çünkü uygulamanın dropdown seçenekleri için sabit referans veri gibi kullanılır.

## Runtime Data

`data/runtime/vehicle_listings.sqlite3`, analizde kullanılan güncel ilan kayıtlarını tutan yerel SQLite veritabanıdır. Kaynak veriler, uygulamaya izinli veya yerel bir veri alma süreciyle aktarılır.

Bu klasör Git'e dahil edilmez. İçindeki veritabanı makineye özel çalışma verisidir.

## Veri Akışı

```text
İzinli kaynaklardan yerel veri aktarımı
  -> vehicle_listings ham tablosunu günceller
  -> cleaning hattı vehicle_listings_clean tablosunu üretir
  -> FastAPI ve React arayüzü temiz tablodan piyasa analizini gösterir
```

## Not

Projenin ana yaklaşımı hazır statik fiyat dataset'i yerine güncel ilan verisiyle piyasa aralığı üretmektir.
