import { Activity, CalendarClock, Database, Landmark } from "lucide-react";
import type { MarketOverview } from "../types";
import { dateTime, money, number, percent } from "../utils/format";
import { EmptyState, LoadingSkeleton } from "./StatePanels";

export function MarketSummary({ data, loading }: { data: MarketOverview | null; loading: boolean }) {
  if (loading) return <section className="summary-grid"><LoadingSkeleton rows={4} /></section>;
  if (!data || data.listing_count === 0) return <EmptyState detail={data?.message} />;
  const metrics = [
    { label: "Medyan piyasa fiyatı", value: money(data.median_price), icon: <Landmark />, emphasis: true },
    { label: "Ortalama fiyat", value: money(data.average_price), icon: <Activity /> },
    { label: "Aktif analiz örneklemi", value: number(data.listing_count), icon: <Database /> },
    { label: "Son veri güncellemesi", value: dateTime(data.last_updated_at), icon: <CalendarClock /> },
  ];
  return <>
    <section className="summary-grid" aria-label="Piyasa özeti">
      {metrics.map((metric) => <article className={`metric-card ${metric.emphasis ? "emphasis" : ""}`} key={metric.label}>
        <span className="metric-icon">{metric.icon}</span><p>{metric.label}</p><strong>{metric.value}</strong>
      </article>)}
    </section>
    <div className="change-strip" aria-label="Piyasa değişim metrikleri">
      <span>30 gün <b>{percent(data.change_30d)}</b></span><span>90 gün <b>{percent(data.change_90d)}</b></span><span>Yıllık <b>{percent(data.change_yoy)}</b></span><small>{data.source_status}</small>
    </div>
  </>;
}
