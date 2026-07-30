import { useState } from "react";
import { VehicleFilters } from "./VehicleFilters";
import type { Filters, ValuationRequest } from "../types";

export function ValuationForm({ onSubmit }: { onSubmit: (payload: ValuationRequest) => void }) {
  const [filters, setFilters] = useState<Filters>({});
  const [year, setYear] = useState("");
  const [mileage, setMileage] = useState("");
  const [askingPrice, setAskingPrice] = useState("");
  const [changedParts, setChangedParts] = useState("");
  const [paintedParts, setPaintedParts] = useState("");

  const submit = () => onSubmit({
    ...filters,
    year: year ? Number(year) : undefined,
    mileage_km: mileage ? Number(mileage) : undefined,
    asking_price: askingPrice ? Number(askingPrice) : undefined,
    changed_parts: changedParts ? Number(changedParts) : undefined,
    painted_parts: paintedParts ? Number(paintedParts) : undefined,
  });

  return <div className="valuation-form">
    <VehicleFilters value={filters} onApply={setFilters} autoApply showRangeFilters={false} />
    <div className="valuation-extras">
      <label className="field"><span>Model yılı</span><input type="number" min="1980" max="2026" value={year} onChange={(event) => setYear(event.target.value)} placeholder="Örn. 2021" /></label>
      <label className="field"><span>Kilometre</span><input type="number" min="0" value={mileage} onChange={(event) => setMileage(event.target.value)} placeholder="Örn. 80000" /></label>
      <label className="field"><span>İstenen fiyat</span><input type="number" min="0" value={askingPrice} onChange={(event) => setAskingPrice(event.target.value)} placeholder="Opsiyonel" /></label>
      <label className="field"><span>Değişen parça</span><input type="number" min="0" max="30" value={changedParts} onChange={(event) => setChangedParts(event.target.value)} placeholder="Örn. 0" /></label>
      <label className="field"><span>Boyalı parça</span><input type="number" min="0" max="30" value={paintedParts} onChange={(event) => setPaintedParts(event.target.value)} placeholder="Örn. 1" /></label>
      <button className="primary-button" onClick={submit}>Araç değerini hesapla</button>
    </div>
  </div>;
}
