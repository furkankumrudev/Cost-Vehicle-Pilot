import { BadgePercent, CalendarRange, Gauge, Sparkles } from "lucide-react";
import type { ValuationResponse } from "../types";
import { money, number, percent } from "../utils/format";
import { EmptyState } from "./StatePanels";

function ConditionAdjustmentCard({ data }: { data: ValuationResponse }) {
  if (data.condition_adjustment_percent == null) return null;
  const unchanged = data.condition_adjustment_percent === 0;
  return <div className="condition-adjustment-card"><div><span className="eyebrow"><BadgePercent size={14} />DURUM ETKİSİ</span><strong>{unchanged ? "Referans durum" : percent(data.condition_adjustment_percent)}</strong></div><p>{data.condition_adjustment_note}</p></div>;
}

function ComparisonSummary({ data }: { data: ValuationResponse }) {
  const summary = data.comparison_summary;
  if (!summary) return null;
  return <section className="comparison-summary">
    <div className="comparison-heading"><div><span className="eyebrow">PİYASA KARŞILAŞTIRMASI</span><h3>Referans ilan grubu</h3></div><p>Sonuçta kullanılan güncel ilan verisi</p></div>
    <div className="comparison-grid">
      <div><span>İşlenen ilan</span><strong>{number(summary.used_listing_count)}</strong><small>benzer kayıt</small></div>
      <div><span><CalendarRange size={14} />Referans yıl</span><strong>{summary.median_year ?? "—"}</strong><small>medyan model yılı</small></div>
      <div><span><Gauge size={14} />Referans kilometre</span><strong>{number(summary.median_mileage_km)} km</strong><small>medyan kilometre</small></div>
    </div>
  </section>;
}

function positionOnScale(value: number, minimum: number, maximum: number) {
  return Math.min(96, Math.max(4, ((value - minimum) / (maximum - minimum)) * 100));
}

function PricePositionScale({ data }: { data: ValuationResponse }) {
  const low = data.recommended_low_price;
  const marketValue = data.estimated_market_value;
  const high = data.recommended_high_price;
  if (low == null || marketValue == null || high == null) return null;

  const askingPrice = data.asking_price_delta_percent == null
    ? null
    : marketValue * (1 + data.asking_price_delta_percent / 100);
  const minimum = Math.min(low, askingPrice ?? low) * 0.94;
  const maximum = Math.max(high, askingPrice ?? high) * 1.06;
  const lowPosition = positionOnScale(low, minimum, maximum);
  const highPosition = positionOnScale(high, minimum, maximum);
  const marketPosition = positionOnScale(marketValue, minimum, maximum);
  const askingPosition = askingPrice == null ? null : positionOnScale(askingPrice, minimum, maximum);

  return <section className="price-position-card">
    <div className="price-position-heading"><div><span className="eyebrow">FİYAT KONUMU</span><h3>Piyasa fiyat dağılımı</h3></div><p>Aracın güncel piyasa aralığındaki yeri</p></div>
    <div className="price-position-values">
      <div><span>Alt bant</span><strong>{money(low)}</strong></div>
      <div><span>Piyasa değeri</span><strong>{money(marketValue)}</strong></div>
      <div><span>Üst bant</span><strong>{money(high)}</strong></div>
    </div>
    <div className="price-scale" aria-label={`Piyasa aralığı ${money(low)} ile ${money(high)} arasında`}>
      <div className="price-scale-band" style={{ left: `${lowPosition}%`, width: `${highPosition - lowPosition}%` }} />
      <span className="price-scale-marker market" style={{ left: `${marketPosition}%` }} title="Tahmini piyasa değeri" />
      {askingPosition != null && <span className="price-scale-marker asking" style={{ left: `${askingPosition}%` }} title="Girdiğiniz fiyat" />}
    </div>
    <div className="price-scale-legend"><span><i className="market" />Tahmini piyasa değeri</span>{askingPosition != null && <span><i className="asking" />Girdiğiniz fiyat</span>}</div>
  </section>;
}

export function ValuationResult({ data }: { data: ValuationResponse | null }) {
  if (!data) return <div className="valuation-placeholder"><Sparkles size={26} /><strong>Aracınızın piyasa değerini hesaplayın</strong><p>Seçtiğiniz kriterlerle eşleşen gerçek ilanlardan bir tahmin oluşturacağız.</p></div>;
  if (data.status === "empty") return <EmptyState title="Güncel piyasa karşılaştırması oluşmadı" detail={data.explanation} />;
  return <section className="valuation-result">
    <div className="result-hero"><span className="eyebrow">TAHMİNİ PİYASA DEĞERİ</span><strong>{money(data.estimated_market_value)}</strong><p>Güncel ilan verisi · {data.confidence} güven</p></div>
    <div className="range-card"><p>Önerilen piyasa aralığı</p><strong>{money(data.recommended_low_price)} — {money(data.recommended_high_price)}</strong><div className="price-rail"><span /><i /></div><small>Düşük <b>Uygun</b> Yüksek</small></div>
    <ConditionAdjustmentCard data={data} />
    <ComparisonSummary data={data} />
    <PricePositionScale data={data} />
  </section>;
}
