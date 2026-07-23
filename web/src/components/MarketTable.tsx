import { ArrowDownUp, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import type { Filters, MarketTableRow } from "../types";
import { money, number, percent } from "../utils/format";
import { EmptyState, ErrorState, LoadingSkeleton } from "./StatePanels";

type Group = "brand" | "body_type" | "fuel_type";

export function MarketTable({ filters }: { filters: Filters }) {
  const [group, setGroup] = useState<Group>("brand");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<keyof MarketTableRow>("listing_count");
  const [descending, setDescending] = useState(true);
  const { data, loading, error } = useAsync(() => api.table(filters, group), [JSON.stringify(filters), group]);
  const rows = useMemo(() => (data?.rows ?? []).filter((row) => row.label.toLocaleLowerCase("tr").includes(search.toLocaleLowerCase("tr"))).sort((a, b) => {
    const aValue = a[sortKey] ?? -Infinity; const bValue = b[sortKey] ?? -Infinity;
    return (aValue < bValue ? -1 : aValue > bValue ? 1 : 0) * (descending ? -1 : 1);
  }), [data, search, sortKey, descending]);
  const sort = (key: keyof MarketTableRow) => { if (sortKey === key) setDescending(!descending); else { setSortKey(key); setDescending(true); } };
  const title = group === "brand" ? "Marka" : group === "body_type" ? "Kasa tipi" : "Yakıt tipi";
  return <section className="section-block table-section"><div className="section-heading"><div><span className="eyebrow">KARŞILAŞTIRMA</span><h2>Piyasa karşılaştırma tablosu</h2><p>Fiyat değişimleri için gerçek tarihsel snapshot birikimi gerekir.</p></div><div className="table-controls"><select aria-label="Gruplama türü" value={group} onChange={(event) => setGroup(event.target.value as Group)}><option value="brand">Markaya göre</option><option value="body_type">Kasa tipine göre</option><option value="fuel_type">Yakıt tipine göre</option></select><label className="search-input"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tabloda ara" /></label></div></div>
    {loading ? <LoadingSkeleton rows={6} /> : error ? <ErrorState detail={error} /> : !rows.length ? <EmptyState detail={data?.message} /> : <div className="table-scroll"><table><thead><tr>{([{ key: "label", text: title }, { key: "average_price", text: "Ortalama fiyat" }, { key: "median_price", text: "Medyan fiyat" }, { key: "listing_count", text: "İlan sayısı" }] as { key: keyof MarketTableRow; text: string }[]).map((column) => <th key={column.key}><button onClick={() => sort(column.key)}>{column.text}<ArrowDownUp size={13} /></button></th>)}<th>Son 30 gün</th><th>Son 90 gün</th><th>Yıllık değişim</th></tr></thead><tbody>{rows.map((row) => <tr key={row.label}><td><strong>{row.label}</strong></td><td>{money(row.average_price)}</td><td>{money(row.median_price)}</td><td>{number(row.listing_count)}</td><td>{percent(row.change_30d)}</td><td>{percent(row.change_90d)}</td><td>{percent(row.change_yoy)}</td></tr>)}</tbody></table></div>}
  </section>;
}
