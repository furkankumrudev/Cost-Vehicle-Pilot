import { useState } from "react";
import { MarketMovers } from "../components/MarketMovers";
import { MarketSummary } from "../components/MarketSummary";
import { MarketTable } from "../components/MarketTable";
import { MethodologySection } from "../components/MethodologySection";
import { PriceTrendChart } from "../components/PriceTrendChart";
import { VehicleFilters } from "../components/VehicleFilters";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import type { Filters } from "../types";

export function MarketTrendsPage() {
  const [filters, setFilters] = useState<Filters>({});
  const { data: overview, loading } = useAsync(() => api.overview(filters), [JSON.stringify(filters)]);
  return <main><section className="hero"><div className="shell"><span className="eyebrow">GÜNCEL PİYASA GÖRÜNÜMÜ</span><h1>İkinci el araç fiyatlarını verilerle takip et</h1><p>Türkiye ikinci el araç ilanlarından oluşturulan güncel piyasa fiyatlarını, değişimleri ve araç karşılaştırmalarını inceleyin.</p></div></section><div className="shell page-content"><MarketSummary data={overview} loading={loading} /><VehicleFilters value={filters} onApply={setFilters} /><MarketMovers /><PriceTrendChart filters={filters} /><MarketTable filters={filters} /><MethodologySection /></div></main>;
}
