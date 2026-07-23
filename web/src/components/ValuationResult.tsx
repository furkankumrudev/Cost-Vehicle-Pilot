import { CheckCircle2, CircleGauge, Sparkles } from "lucide-react";
import type { ValuationResponse } from "../types";
import { money, number, percent } from "../utils/format";
import { EmptyState } from "./StatePanels";

export function ValuationResult({ data }: { data: ValuationResponse | null }) {
  if (!data) return <div className="valuation-placeholder"><Sparkles size={26} /><strong>Aracınızın piyasa değerini hesaplayın</strong><p>Seçtiğiniz kriterlerle eşleşen gerçek ilanlardan bir tahmin oluşturacağız.</p></div>;
  if (data.status === "empty") return <EmptyState title="Değerleme oluşturulamadı" detail={data.explanation} />;
  return <section className="valuation-result"><div className="result-hero"><span className="eyebrow">TAHMİNİ PİYASA DEĞERİ</span><strong>{money(data.estimated_market_value)}</strong><p>{data.listing_count} benzer ilan · {data.confidence} güven</p></div><div className="range-card"><p>Önerilen piyasa aralığı</p><strong>{money(data.recommended_low_price)} — {money(data.recommended_high_price)}</strong><div className="price-rail"><span /><i /></div><small>Düşük <b>Uygun</b> Yüksek</small></div><div className="valuation-notes"><p><CircleGauge size={18} />{data.price_assessment ?? "İstenen fiyat girilmedi"}{data.asking_price_delta_percent != null ? ` (${percent(data.asking_price_delta_percent)})` : ""}</p><p><CheckCircle2 size={18} />{data.explanation}</p></div><div className="similar-listings"><h3>Benzer ilanlar</h3>{data.similar_listings.map((listing) => <article key={listing.id ?? `${listing.title}-${listing.price}`}><div><strong>{listing.title}</strong><span>{listing.year ?? "—"} · {number(listing.mileage_km)} km · {listing.city ?? "Konum yok"}</span></div><b>{money(listing.price)}</b></article>)}</div></section>;
}
