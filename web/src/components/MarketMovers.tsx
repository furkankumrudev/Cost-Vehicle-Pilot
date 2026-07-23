import { ArrowDownRight, ArrowUpRight, CarFront } from "lucide-react";
import { useState } from "react";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { money, number, percent } from "../utils/format";
import { EmptyState, ErrorState, LoadingSkeleton } from "./StatePanels";

export function MarketMovers() {
  const [direction, setDirection] = useState<"up" | "down">("down");
  const { data, loading, error } = useAsync(() => api.movers(direction), [direction]);
  return <section className="section-block"><div className="section-heading"><div><span className="eyebrow">PİYASA HAREKETİ</span><h2>Piyasayı Hareketlendiren Araçlar</h2><p>Oranlar yalnızca ayrı günlerde kaydedilmiş gerçek piyasa özetlerinden hesaplanır.</p></div><div className="segmented" role="group" aria-label="Hareket yönü"><button className={direction === "down" ? "selected" : ""} onClick={() => setDirection("down")}>En çok düşenler</button><button className={direction === "up" ? "selected" : ""} onClick={() => setDirection("up")}>En çok yükselenler</button></div></div>
    {loading ? <LoadingSkeleton rows={2} /> : error ? <ErrorState detail={error} /> : !data?.available ? <EmptyState title="Hareket verisi henüz oluşmadı" detail={data?.message} /> : <div className="mover-grid">{data.items.map((item) => <article className="mover-card" key={item.label}><span className="vehicle-token"><CarFront size={21} /></span><div><p>{item.label}</p><strong>{money(item.average_price)}</strong><small>{number(item.listing_count)} ilan</small></div><b className={item.direction === "up" ? "positive" : "negative"}>{item.direction === "up" ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />}{percent(item.change_percent)}</b></article>)}</div>}
  </section>;
}
