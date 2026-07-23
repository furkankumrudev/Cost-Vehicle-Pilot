# Data Strategy

## Amaç

ArabamFiyat.com'un veri stratejisi, kullanıcının seçtiği araç özelliklerine göre güncel ve benzer ilanları analiz ederek piyasa fiyat aralığı üretmektir.

## Ana Karar

Proje hazır ve eski bir public CSV veri setine bağlı kalmayacaktır. Bunun yerine veri akışı şu şekilde tasarlanmıştır:

```text
Araç özellikleri formu
  -> sorgu oluşturma
  -> güncel ilan toplama
  -> SQLite kayıt katmanı
  -> benzer ilan filtreleme
  -> fiyat dağılımı ve piyasa aralığı
```

## Katalog Verisi

Arayüzde marka, seri ve model/paket seçimlerinin hazır gelmesi için `data/reference/vehicle_catalog.json` kullanılır.

Bu dosya statik bir eğitim datası değildir; yalnızca kullanıcı deneyimini iyileştiren referans katalogdur.

## Güncel İlan Verisi

Scraper modülü, seçilen araç özelliklerine göre arama yapıp ilanları normalize ederek SQLite veritabanına yazar.

Varsayılan lokal veritabanı:

```text
data/runtime/vehicle_listings.sqlite3
```

## Sorumlu Kullanım

Canlı ilan sitelerinden veri toplama teknik ve hukuki riskler içerebilir. Bu nedenle proje anlatımında veri toplama katmanı; kontrollü prototip, izinli veri kaynakları, resmi API veya partner veri akışlarına uyarlanabilir mimari olarak konumlandırılır.

## MVP Değeri

İlk MVP için model eğitimi şart değildir. Kullanıcıya değer üreten ilk çıktı:

- benzer ilan sayısı
- fiyat dağılımı
- medyan fiyat
- önerilen alt/üst piyasa aralığı
- benzer ilan listesi

Bu yaklaşım ürünün doğrudan kullanıcı problemine cevap vermesini sağlar.
