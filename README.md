# Cost Vehicle Pilot

Cost Vehicle Pilot, ikinci el araç piyasasında alıcı ve satıcıların daha bilinçli fiyat kararları verebilmesi için geliştirilen yapay zeka destekli adil fiyat tahmin ve piyasa trend analiz platformudur.

## Takım Bilgileri

**Takım İsmi:** Furkan Kumru

Bu proje bireysel olarak geliştirilmektedir.

| Rol | Sorumlu |
| --- | --- |
| Product Owner | Furkan Kumru |
| Scrum Master | Furkan Kumru |
| Developer | Furkan Kumru |
| Data Analyst / ML Developer | Furkan Kumru |
| UI/UX ve Dokümantasyon | Furkan Kumru |

## Ürün Açıklaması

İkinci el araç piyasasında ilan fiyatları; marka, model, yıl, kilometre, yakıt tipi, vites türü, şehir, hasar durumu ve piyasa talebi gibi birçok faktöre göre değişmektedir. Bu değişkenlik, kullanıcıların bir aracın gerçek piyasa değerini anlamasını zorlaştırır.

Cost Vehicle Pilot, geçmiş araç verilerini analiz ederek kullanıcının girdiği araç bilgilerine göre tahmini adil piyasa değerini hesaplar. Platform; fiyat tahmini, benzer araç karşılaştırması, fiyat trend grafikleri ve yapay zeka destekli yorumlar ile kullanıcıya karar verme sürecinde rehberlik eder.

## Problem

İkinci el araç alım-satım sürecinde kullanıcılar çoğu zaman şu sorulara net cevap bulmakta zorlanır:

- Bu araç gerçek piyasa değerinde mi?
- İlan fiyatı benzer araçlara göre yüksek mi?
- Satıcı olarak aracı hangi fiyat aralığında ilana koymalıyım?
- Alıcı olarak pazarlığa hangi seviyeden başlamalıyım?
- Kilometre, model yılı, şehir ve hasar durumu fiyatı ne kadar etkiliyor?

## Çözüm

Cost Vehicle Pilot, araç bilgilerini makine öğrenmesi tabanlı fiyat tahmin modeliyle analiz eder ve kullanıcıya anlaşılır bir karar destek çıktısı sunar:

- Tahmini adil piyasa değeri
- Tahmini fiyat aralığı
- Piyasa durumu sınıflandırması
- Benzer araçlarla karşılaştırma
- Fiyat trend grafikleri
- Fiyatı etkileyen temel faktörler
- Alıcı ve satıcı için yapay zeka destekli kısa yorum

## Hedef Kitle

- Aracını satmak isteyen bireysel kullanıcılar
- İkinci el araç satın almak isteyen alıcılar
- İlan fiyatının piyasa koşullarına uygunluğunu kontrol etmek isteyen kullanıcılar
- Galeriler ve küçük ölçekli araç satıcıları
- İkinci el araç piyasasındaki fiyat trendlerini analiz etmek isteyen kişiler

## Ürün Özellikleri

- Araç bilgisi giriş formu
- Marka, model, yıl, kilometre, yakıt tipi, vites, şehir ve hasar durumuna göre fiyat tahmini
- Makine öğrenmesi tabanlı adil piyasa değeri hesaplama
- Tahmini fiyat aralığı gösterimi
- İlan fiyatının piyasanın altında, piyasa seviyesinde veya üzerinde olduğunu sınıflandırma
- Benzer araçlarla karşılaştırma
- Marka, model ve yıl bazlı fiyat trend grafikleri
- Kilometre ve model yılına göre fiyat değişim analizi
- Fiyatı etkileyen temel faktörlerin gösterimi
- Yapay zeka destekli değerlendirme yorumu
- Satıcılar için önerilen satış fiyatı
- Alıcılar için pazarlık başlangıç önerisi
- Kullanıcı dostu dashboard arayüzü

## Kullanılacak Teknolojiler

Planlanan teknoloji seti:

- Python
- Pandas / NumPy
- Scikit-learn
- Matplotlib / Seaborn / Plotly
- Streamlit veya Flask/FastAPI
- GitHub Projects / Issues
- Jupyter Notebook

Teknoloji seçimi geliştirme sürecinde veri seti, model ihtiyacı ve canlıya alma kararına göre güncellenebilir.

## Veri Seti

İlk MVP kapsamında public bir ikinci el araç fiyat veri seti kullanılmaktadır.

Kaynak: https://raw.githubusercontent.com/ybifoundation/Dataset/main/Car%20Price.csv

Ham veri `data/raw/used_car_prices.csv` altında, temizlenmiş veri ise `data/processed/used_car_prices_clean.csv` altında tutulmaktadır. Veri temizleme süreci `src/data_preprocessing.py` script'i ile tekrar üretilebilir yapıdadır.

Mevcut veri seti Türkiye odaklı değildir ve fiyatlar INR para birimindedir. Bu veri, ilk teknik MVP ve model geliştirme süreci için kullanılacaktır. Mimari daha sonra Türkiye odaklı dataset veya API destekli veri akışı ile değiştirilebilecek şekilde tasarlanmaktadır.

Detaylar:

- [Data README](data/README.md)
- [Data Strategy](docs/data-strategy.md)
- [Data Dictionary](docs/data-dictionary.md)

## Güncel Veri Toplama Katmanı

Cost Vehicle Pilot yalnızca statik bir veri setine bağlı kalmayacak şekilde tasarlanmaktadır. Projeye Sahibinden arama sonuçlarından güncel araç ilanlarını toplayabilecek bir veri toplama prototipi eklenmiştir.

İlk prototip SQLite veritabanına yazar:

```text
data/runtime/vehicle_listings.sqlite3
```

Örnek komut:

```bash
python -m src.ingestion.sahibinden_scraper --query "Renault Clio" --year-min 2016 --year-max 2018 --max-pages 1
```

Bu katman, bootcamp MVP'sinde güncel veri akışı mimarisini göstermek için kullanılacaktır. Scraping işlemleri dikkatli, sınırlı ve kaynak sitenin kurallarına uygun şekilde ele alınmalıdır. Uzun vadede aynı mimari resmi API, izinli veri sağlayıcıları veya partner veri akışlarıyla çalışabilecek şekilde genişletilebilir.

Detaylar: [Scraper Strategy](docs/scraper-strategy.md)
## Makine Öğrenmesi Yaklaşımı

İlk MVP kapsamında regresyon modelleri ile araç fiyat tahmini yapılması planlanmaktadır.

Planlanan adımlar:

1. Veri setinin bulunması veya oluşturulması
2. Eksik ve hatalı verilerin temizlenmesi
3. Kategorik değişkenlerin modele uygun hale getirilmesi
4. Baseline regresyon modelinin kurulması
5. Farklı modellerin performans karşılaştırması
6. Model sonuçlarının hata metrikleriyle değerlendirilmesi
7. Fiyatı etkileyen değişkenlerin analiz edilmesi
8. Tahmin sonucunun kullanıcı dostu bir arayüzde gösterilmesi

## Product Backlog

| ID | User Story | Öncelik | Durum |
| --- | --- | --- | --- |
| PB-01 | Kullanıcı olarak araç bilgilerini girebilmek istiyorum. | High | Todo |
| PB-02 | Kullanıcı olarak araç için tahmini adil piyasa değerini görmek istiyorum. | High | Todo |
| PB-03 | Kullanıcı olarak tahmini fiyat aralığını görmek istiyorum. | High | Todo |
| PB-04 | Kullanıcı olarak ilan fiyatının piyasanın altında veya üzerinde olduğunu anlayabilmek istiyorum. | High | Todo |
| PB-05 | Kullanıcı olarak benzer araçlarla karşılaştırma yapabilmek istiyorum. | Medium | Todo |
| PB-06 | Kullanıcı olarak fiyat trend grafiklerini incelemek istiyorum. | Medium | Todo |
| PB-07 | Kullanıcı olarak fiyatı etkileyen ana faktörleri görmek istiyorum. | Medium | Todo |
| PB-08 | Satıcı olarak önerilen satış fiyatını görmek istiyorum. | Medium | Todo |
| PB-09 | Alıcı olarak pazarlık başlangıç önerisi almak istiyorum. | Medium | Todo |
| PB-10 | Geliştirici olarak veri temizleme ve model eğitim sürecini dokümante etmek istiyorum. | High | Todo |
| PB-11 | Geliştirici olarak sprint süreçlerini GitHub üzerinde belgelemek istiyorum. | High | In Progress |
| PB-12 | Kullanıcı olarak ürünü basit bir web arayüzünden kullanmak istiyorum. | High | Todo |

## Sprint Planı

### Sprint 1

Odak: Ürün fikrinin netleştirilmesi, veri araştırması, proje iskeleti ve ilk analiz çalışmaları.

- Ürün vizyonunun yazılması
- Hedef kitlenin belirlenmesi
- Product backlog hazırlanması
- Veri seti araştırması
- İlk veri temizleme planı
- Repo ve dokümantasyon yapısının oluşturulması

Detaylar: [Sprint 1](project-management/sprint-1/sprint-1.md)

### Sprint 2

Odak: Veri işleme, model geliştirme ve ilk tahmin akışının oluşturulması.

- Veri temizleme
- Feature engineering
- Baseline model
- Model performans analizi
- İlk fiyat tahmin fonksiyonu
- İlk grafik denemeleri

Detaylar: [Sprint 2](project-management/sprint-2/sprint-2.md)

### Sprint 3

Odak: Arayüz, ürün bütünlüğü, demo ve final teslim hazırlığı.

- Web arayüzü
- Dashboard ekranları
- Tahmin sonucu ve AI yorum bölümü
- Ürün ekran görüntüleri
- Demo senaryosu
- Final README düzenlemesi
- 3 dakikalık proje videosu hazırlığı

Detaylar: [Sprint 3](project-management/sprint-3/sprint-3.md)

## Proje Yönetimi

Bootcamp süreci boyunca sprint çıktıları, daily scrum notları, sprint board güncellemeleri, ürün durumu, sprint review ve retrospective dokümanları `project-management` klasörü altında tutulacaktır.

## Repo Yapısı

```text
Cost-Vehicle-Pilot/
  README.md
  docs/
    product-vision.md
    target-audience.md
    market-research.md
  project-management/
    sprint-1/
    sprint-2/
    sprint-3/
  data/
  notebooks/
  src/
  assets/
    screenshots/
```

## Durum

Proje geliştirme aşamasındadır. İlk sprint kapsamında ürün vizyonu, backlog ve veri araştırması hazırlanmaktadır.

