import { useState } from "react";
import { VehicleFilters } from "./VehicleFilters";
import type { Filters, ValuationRequest } from "../types";

export function ValuationForm({ onSubmit }: { onSubmit: (payload: ValuationRequest) => void }) {
  const [filters, setFilters] = useState<Filters>({});
  const [year, setYear] = useState(""); const [mileage, setMileage] = useState(""); const [askingPrice, setAskingPrice] = useState("");
  return <div className="valuation-form"><VehicleFilters value={filters} onApply={setFilters} /><div className="valuation-extras"><label className="field"><span>Model yılı</span><input type="number" min="1980" max="2026" value={year} onChange={(event) => setYear(event.target.value)} placeholder="Örn. 2021" /></label><label className="field"><span>Kilometre</span><input type="number" min="0" value={mileage} onChange={(event) => setMileage(event.target.value)} placeholder="Örn. 80000" /></label><label className="field"><span>İstenen fiyat (opsiyonel)</span><input type="number" min="0" value={askingPrice} onChange={(event) => setAskingPrice(event.target.value)} placeholder="Örn. 1250000" /></label><button className="primary-button" onClick={() => onSubmit({ ...filters, year: year ? Number(year) : undefined, mileage_km: mileage ? Number(mileage) : undefined, asking_price: askingPrice ? Number(askingPrice) : undefined })}>Araç değerini hesapla</button></div></div>;
}
