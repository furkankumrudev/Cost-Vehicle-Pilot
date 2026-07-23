import { AlertCircle, DatabaseZap, LoaderCircle } from "lucide-react";

export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return <div className="skeleton-block" aria-label="Yükleniyor">{Array.from({ length: rows }, (_, index) => <span key={index} />)}</div>;
}

export function EmptyState({ title = "Yeterli veri yok", detail }: { title?: string; detail?: string | null }) {
  return <div className="state-panel empty"><DatabaseZap size={25} /><div><strong>{title}</strong><p>{detail ?? "Seçilen kriterler için gösterilecek gerçek piyasa verisi bulunamadı."}</p></div></div>;
}

export function ErrorState({ detail }: { detail: string }) {
  return <div className="state-panel error"><AlertCircle size={25} /><div><strong>Veri bağlantısı kurulamadı</strong><p>{detail}</p></div></div>;
}

export function BusyButton({ children }: { children: string }) {
  return <span className="busy-label"><LoaderCircle size={16} />{children}</span>;
}
