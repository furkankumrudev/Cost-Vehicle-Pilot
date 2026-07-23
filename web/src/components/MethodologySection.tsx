import { BadgeInfo, ShieldCheck } from "lucide-react";

export function MethodologySection() {
  return <section id="metodoloji" className="methodology section-block"><div><span className="eyebrow"><BadgeInfo size={15} />METODOLOJİ</span><h2>Fiyatlar nasıl hesaplanıyor?</h2><p>ArabamFiyat.com, temizlenmiş ikinci el ilanlarını kullanır. Benzer araçlar yıl, kilometre, model yakınlığı ve veri güncelliğine göre değerlendirilir; olağandışı fiyatlar analizden çıkarılır.</p></div><aside><ShieldCheck size={24} /><p>Gösterilen değerler mevcut ilan verilerine dayalı piyasa tahminleridir. Kesin satış fiyatı; aracın donanımı, kondisyonu, hasar durumu, konumu ve piyasa koşullarına göre değişebilir.</p></aside></section>;
}
