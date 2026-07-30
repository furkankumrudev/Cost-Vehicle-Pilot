# Model Kartı - Kondisyon Etkisi Modeli

## Amaç

Bu model, ikinci el aracın boya ve değişen parça bilgisinin fiyat üzerindeki göreli etkisini tahmin eder. Güncel TL fiyatını tek başına üretmez. Güncel piyasa değeri, ArabamFiyat.com'un temizlenmiş güncel ilan havuzundan hesaplanır; modelin ürettiği katsayı bu güncel değere uygulanır.

Bu ayrım önemlidir: eğitim verisindeki fiyatlar tarihsel olduğu için modelin eski TL tahminini güncel fiyat diye göstermek doğru değildir.

## Model ve Girdi Alanları

- Algoritma: CatBoostRegressor
- Kategorik alanlar: `marka`, `seri`, `model`
- Sayısal alanlar: `yil`, `kilometre`, `degisen_sayisi`, `boyali_sayisi`
- Referans karşılaştırması: aynı araç için `0 boya / 0 değişen` durumu ile kullanıcının girdiği kondisyon durumu karşılaştırılır.
- Güvenlik sınırı: koşul katsayısı `0,65` ile `1,00` arasında tutulur. Model fiyat artışı üretmez ve en fazla yüzde 35 indirim uygular.

## Eğitim Verisi

Eğitim, Kaggle'daki Türkiye ikinci el araç ilan verisiyle yapılır. Bu veri, lisans ve boyut nedeniyle repoya dahil edilmez. Yerel geliştirmede kullanılan dosya `car_price_prediction.csv` olarak proje kökünde bulunur.

27 Temmuz 2026 tarihli eğitim çalıştırmasında:

| Aşama | Satır |
| --- | ---: |
| Ham veri | 50.755 |
| Zorunlu alanları dolu kayıt | 40.339 |
| Sınır kontrolleri sonrası | 40.257 |
| Grup içi uç fiyat temizliği sonrası | 40.118 |
| Eğitim seti | 32.094 |
| Test seti | 8.024 |

## Son Eğitim Metrikleri

| Metrik | Değer |
| --- | ---: |
| MAE | 124.771 TL |
| Medyan mutlak hata | 49.903 TL |
| RMSE | 670.356 TL |
| SMAPE | %11,35 |
| R2 | 0,776 |
| Tahminin gerçek fiyata %10 yakınlığı | %59,53 |
| Tahminin gerçek fiyata %20 yakınlığı | %84,83 |

Bu metrikler tarihsel veri üzerindeki fiyat tahmin performansını gösterir. Boya/değişen katsayısının güncel pazardaki doğruluğu için ayrı bir saha doğrulaması yapılmamıştır; bu nedenle sonuç ekranında katsayı, kesin ekspertiz sonucu olarak sunulmaz.

## Tekrar Eğitim

1. Kaggle CSV dosyasını proje köküne `car_price_prediction.csv` adıyla ekleyin.
2. Sanal ortam ve bağımlılıkları kurun.
3. Aşağıdaki komutu çalıştırın:

```bat
scripts\train_price_model.bat
```

Komut modeli ve metrik raporunu `data/models/kaggle_price_effect/` altında üretir. Bu artefaktlar yerel çalışma çıktısıdır ve Git'e eklenmez.

## Sınırlamalar

- Eğitim verisi güncel ilan fiyatı üretmek için kullanılmaz.
- Modelin görmediği veya çok az gördüğü marka/model kombinasyonlarında kondisyon etkisi daha belirsizdir.
- Boya ve değişen sayısı, hasarın niteliğini veya ekspertiz sonucunu tam olarak temsil etmez.
- Güncel piyasa değeri, veri havuzunun güncelliğine ve benzer ilan sayısına bağlıdır.
- Sonuç karar desteğidir; kesin satış veya satın alma fiyatı değildir.
