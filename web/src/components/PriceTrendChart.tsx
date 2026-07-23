import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import type { Filters } from "../types";
import { money, number, shortDate } from "../utils/format";
import { EmptyState, ErrorState, LoadingSkeleton } from "./StatePanels";

type Range = "30" | "90" | "180" | "365" | "all" | "custom";
const startFor = (range: Range) => { if (range === "all" || range === "custom") return undefined; const now = new Date(); now.setDate(now.getDate() - Number(range)); return now.toISOString().slice(0, 10); };

export function PriceTrendChart({ filters }: { filters: Filters }) {
  const [range, setRange] = useState<Range>("all");
  const [stat, setStat] = useState<"median" | "average">("median");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const startDate = range === "custom" ? customStart : startFor(range);
  const endDate = range === "custom" ? customEnd : undefined;
  const { data, loading, error } = useAsync(() => api.trend(filters, startDate, endDate), [JSON.stringify(filters), startDate, endDate]);
  return <section className="chart-card section-block"><div className="section-heading"><div><span className="eyebrow">FİYAT TRENDİ</span><h2>İkinci El Araç Fiyat Trendi</h2><p>{data?.label ?? "İlan tarihine göre fiyat görünümü"}</p></div><div className="segmented"><button className={stat === "median" ? "selected" : ""} onClick={() => setStat("median")}>Medyan</button><button className={stat === "average" ? "selected" : ""} onClick={() => setStat("average")}>Ortalama</button></div></div>
    <div className="chart-toolbar"><div className="range-buttons">{(["30", "90", "180", "365", "all", "custom"] as Range[]).map((item) => <button key={item} className={range === item ? "selected" : ""} onClick={() => setRange(item)}>{({ "30": "30 Gün", "90": "90 Gün", "180": "6 Ay", "365": "1 Yıl", all: "Tümü", custom: "Özel" })[item]}</button>)}</div>{range === "custom" && <div className="date-controls"><label>Başlangıç<input type="date" value={customStart} onChange={(event) => setCustomStart(event.target.value)} /></label><label>Bitiş<input type="date" value={customEnd} onChange={(event) => setCustomEnd(event.target.value)} /></label></div>}</div>
    {loading ? <LoadingSkeleton rows={5} /> : error ? <ErrorState detail={error} /> : !data?.available ? <EmptyState title="Geçmiş trend oluşmadı" detail={data?.message} /> : <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><LineChart data={data.points} margin={{ top: 12, right: 14, left: 16, bottom: 6 }}><CartesianGrid stroke="#e7edf5" strokeDasharray="3 4" /><XAxis dataKey="date" tickFormatter={shortDate} tickLine={false} axisLine={false} minTickGap={30} /><YAxis tickFormatter={(value) => `${number(value / 1_000_000)} Mn`} tickLine={false} axisLine={false} width={52} /><Tooltip formatter={(value, name) => [money(Number(value)), name === "median_price" ? "Medyan fiyat" : "Ortalama fiyat"]} labelFormatter={(value) => `${shortDate(String(value))} · ${number(data.points.find((point) => point.date === value)?.listing_count)} ilan`} /><Legend formatter={(value) => value === "median_price" ? "Medyan fiyat" : "Ortalama fiyat"} /><Line type="monotone" dataKey={stat === "median" ? "median_price" : "average_price"} stroke="#2563eb" strokeWidth={3} dot={false} activeDot={{ r: 5 }} /></LineChart></ResponsiveContainer></div>}
  </section>;
}
