import { BadgeInfo, Database, LineChart, ScanSearch, ShieldCheck } from "lucide-react";

const steps = [
  { icon: Database, number: "01", title: "Veriyi hazırlarız", detail: "Tekrarlanan, eksik veya güvenilir olmayan kayıtları ayırırız." },
  { icon: ScanSearch, number: "02", title: "Piyasayı karşılaştırırız", detail: "Marka, seri, model, yıl ve kilometre bağlamında ilanları değerlendiririz." },
  { icon: LineChart, number: "03", title: "Sonucu görünür kılarız", detail: "Fiyat dağılımı, medyan ve piyasa aralığını birlikte sunarız." },
];

export function MethodologySection() {
  return <section id="metodoloji" className="methodology section-block">
    <div className="methodology-intro">
      <span className="eyebrow"><BadgeInfo size={15} />PROJE HAKKINDA</span>
      <h2>İkinci el araç piyasasını daha anlaşılır hale getiriyoruz.</h2>
      <p>ArabamFiyat.com, temizlenmiş ilan verisini yalnızca tek bir ortalamaya indirgemez. İlanların nasıl dağıldığını, hangi fiyat aralığında yoğunlaştığını ve seçtiğiniz aracın bu piyasa içindeki konumunu birlikte gösterir.</p>
    </div>

    <div className="methodology-steps" aria-label="Analiz süreci">
      {steps.map(({ icon: Icon, number, title, detail }) => <article key={number}>
        <span className="methodology-step-icon"><Icon size={18} /></span>
        <div><small>{number}</small><h3>{title}</h3><p>{detail}</p></div>
      </article>)}
    </div>

    <div className="methodology-details">
      <article><span>VERİ KALİTESİ</span><h3>Temizlenmiş ilan verisi</h3><p>Fiyat, kilometre, model yılı ve marka bilgileri tutarlılık kontrollerinden geçirilir. Tekrarlayan kayıtlar ve piyasa temsilini bozabilecek aşırı fiyatlar analizden çıkarılır.</p></article>
      <article><span>ANALİZ YAKLAŞIMI</span><h3>İhtiyaca göre referans grubu</h3><p>Yıl ve kilometre girilmediğinde seçilen modeldeki piyasa bütünü değerlendirilir. Bu bilgiler verildiğinde ise yakın özellikteki ilanlardan daha dar bir karşılaştırma grubu oluşturulur.</p></article>
      <article><span>DEĞERLEME SINIRI</span><h3>Karar desteği, satış garantisi değil</h3><p>Sonuçlar mevcut ilan fiyatlarından üretilen piyasa göstergeleridir. Donanım, kondisyon, hasar geçmişi, konum ve satıcı beklentisi nihai satış fiyatını değiştirebilir.</p></article>
    </div>

    <aside className="methodology-note"><ShieldCheck size={23} /><div><strong>Şeffaf değerlendirme</strong><p>Her değerleme sonucunda kaç ilanın eşleştiği, kaç kaydın analize girdiği ve fiyat dağılımının nasıl oluştuğu açıkça gösterilir.</p></div></aside>
  </section>;
}
