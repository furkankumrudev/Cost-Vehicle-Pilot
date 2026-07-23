import { RotateCcw, SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CatalogOption, Filters } from "../types";

const EMPTY: Filters = {};
const optionFields = ["body_type", "fuel_type", "transmission"] as const;
type Props = { value: Filters; onApply: (filters: Filters) => void };

function Select({ label, value, options, disabled, onChange }: { label: string; value?: string; options: CatalogOption[]; disabled?: boolean; onChange: (value: string) => void }) {
  return <label className="field"><span>{label}</span><select value={value ?? ""} disabled={disabled} onChange={(event) => onChange(event.target.value)}><option value="">Tümü</option>{options.map((option) => <option key={option.name} value={option.name}>{option.name}{option.listing_count ? ` (${option.listing_count})` : ""}</option>)}</select></label>;
}

export function VehicleFilters({ value, onApply }: Props) {
  const [draft, setDraft] = useState<Filters>(value);
  const [brands, setBrands] = useState<CatalogOption[]>([]);
  const [series, setSeries] = useState<CatalogOption[]>([]);
  const [models, setModels] = useState<CatalogOption[]>([]);
  const [options, setOptions] = useState<Record<string, CatalogOption[]>>({});
  useEffect(() => { api.brands().then((result) => setBrands(result.items)).catch(() => setBrands([])); }, []);
  useEffect(() => {
    setSeries([]); setModels([]);
    if (draft.brand) api.series(draft.brand).then((result) => setSeries(result.items)).catch(() => setSeries([]));
  }, [draft.brand]);
  useEffect(() => {
    setModels([]);
    if (draft.brand && draft.series) api.models(draft.brand, draft.series).then((result) => setModels(result.items)).catch(() => setModels([]));
  }, [draft.brand, draft.series]);
  useEffect(() => { optionFields.forEach((field) => api.options(field).then((result) => setOptions((current) => ({ ...current, [field]: result.items }))).catch(() => undefined)); }, []);
  const change = (key: keyof Filters, next: string) => setDraft((current) => {
    const updated = { ...current, [key]: next || undefined };
    if (key === "brand") { delete updated.series; delete updated.model; }
    if (key === "series") delete updated.model;
    return updated;
  });
  return <section className="filter-panel" aria-label="Araç filtreleri">
    <div className="section-heading compact"><div><span className="eyebrow"><SlidersHorizontal size={15} />ARAÇ FİLTRELERİ</span><h2>Piyasayı daraltın</h2></div><button className="text-button" onClick={() => { setDraft(EMPTY); onApply(EMPTY); }}><RotateCcw size={15} />Filtreleri temizle</button></div>
    <div className="filter-grid">
      <Select label="Marka" value={draft.brand} options={brands} onChange={(next) => change("brand", next)} />
      <Select label="Seri" value={draft.series} options={series} disabled={!draft.brand} onChange={(next) => change("series", next)} />
      <Select label="Model" value={draft.model} options={models} disabled={!draft.series} onChange={(next) => change("model", next)} />
      <Select label="Kasa tipi" value={draft.body_type} options={options.body_type ?? []} onChange={(next) => change("body_type", next)} />
      <Select label="Yakıt" value={draft.fuel_type} options={options.fuel_type ?? []} onChange={(next) => change("fuel_type", next)} />
      <Select label="Vites" value={draft.transmission} options={options.transmission ?? []} onChange={(next) => change("transmission", next)} />
      <label className="field"><span>Minimum model yılı</span><input type="number" min="1980" max="2026" value={draft.year_min ?? ""} onChange={(event) => setDraft((current) => ({ ...current, year_min: event.target.value ? Number(event.target.value) : undefined }))} placeholder="Örn. 2018" /></label>
      <label className="field"><span>Maksimum model yılı</span><input type="number" min="1980" max="2026" value={draft.year_max ?? ""} onChange={(event) => setDraft((current) => ({ ...current, year_max: event.target.value ? Number(event.target.value) : undefined }))} placeholder="Örn. 2024" /></label>
      <label className="field"><span>Maksimum kilometre</span><input type="number" min="0" value={draft.mileage_max ?? ""} onChange={(event) => setDraft((current) => ({ ...current, mileage_max: event.target.value ? Number(event.target.value) : undefined }))} placeholder="Örn. 100000" /></label>
      <button className="primary-button filter-submit" onClick={() => onApply(draft)}>Analizi güncelle</button>
    </div>
  </section>;
}
