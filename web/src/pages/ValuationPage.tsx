import { useState } from "react";
import { ValuationForm } from "../components/ValuationForm";
import { ValuationResult } from "../components/ValuationResult";
import { api } from "../api/client";
import type { ValuationRequest, ValuationResponse } from "../types";
import { ErrorState, LoadingSkeleton } from "../components/StatePanels";

export function ValuationPage() {
  const [result, setResult] = useState<ValuationResponse | null>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  const submit = (payload: ValuationRequest) => { setLoading(true); setError(null); api.valuation(payload).then(setResult).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false)); };
  return <main><section className="hero valuation-hero"><div className="shell"><span className="eyebrow">ARAÇ DEĞERLEME</span><h1>Aracınızın piyasa değerini görün</h1><p>Benzer ilanlar, fiyat dağılımı ve aracınızın piyasa konumu ile daha bilinçli karar verin.</p></div></section><div className="shell page-content"><ValuationForm onSubmit={submit} />{loading ? <LoadingSkeleton rows={5} /> : error ? <ErrorState detail={error} /> : <ValuationResult data={result} />}</div></main>;
}
