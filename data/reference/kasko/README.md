# Kasko Referans Değer Listeleri

Bu klasör, TSB'nin aylık yayımladığı kasko değer listesi dosyalarının bırakıldığı yerdir.

Günlük bakım hattı her çalıştığında bu klasöre bakar ve **henüz içeri aktarılmamış dönemleri** aktarır. Yeni dönem yoksa adım `skipped` olarak kaydedilir; bu bir hata değildir.

## Kullanım

İndirdiğin dosyayı dönem bilgisi adında olacak şekilde buraya koy:

```text
data/reference/kasko/kasko_2026_09.xlsx
data/reference/kasko/Kasko Değer Listesi Eylül 2026.xlsx
```

Her iki adlandırma da tanınır. Dosya adından dönem çıkarılamazsa aktarım reddedilir ve `--period 2026-09` ile açıkça vermen istenir; sistem tahminde bulunmaz.

## Sütunlar

Aktarım şu sütunları arar ve yazım farklarını (büyük/küçük harf, Türkçe karakter, boşluk) tolere eder:

| Mantıksal alan | Tanınan yazımlar |
| --- | --- |
| `brand` | Marka, Marka Adı |
| `model_name` | Tip, Tip Adı, Model, Model Adı |
| `model_year` | Model Yılı, Yıl |
| `reference_value` | Kasko Değeri, Kasko Bedeli, Değer, Bedel |
| `vehicle_code` | Araç Kodu, Kod (opsiyonel) |

Yayımlanan dosyanın başlıkları bunlardan farklıysa aktarım **sessizce yanlış sütunu okumaz**; hata verir ve dosyada gördüğü başlıkları listeler. O durumda eşlemeyi açıkça verebilirsin:

```bash
./scripts/import_reference_values.sh data/reference/kasko/liste.xlsx \
    --db-path data/runtime/vehicle_listings.sqlite3 \
    --column reference_value="Kasko Bedeli (TL)"
```

## Önemli

Bu değerler **sigorta referans değeridir, ilan satış fiyatı değildir.** Ayrı bir tabloda (`reference_vehicle_values`) tutulur ve ilan tablolarıyla karıştırılmaz.

Dosyaların kendisi Git'e dahil edilmez.
