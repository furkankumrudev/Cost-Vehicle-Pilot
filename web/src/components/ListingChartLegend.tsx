type LegendItemProps = {
  color: string;
  label: string;
  detail: string;
};

function LegendItem({ color, label, detail }: LegendItemProps) {
  return <span className="listing-legend-item" tabIndex={0}>
    <i className="listing-legend-swatch" style={{ backgroundColor: color }} aria-hidden="true" />
    {label}
    <span className="listing-legend-tooltip" role="tooltip">{detail}</span>
  </span>;
}

export function ListingChartLegend({ showClean }: { showClean: boolean }) {
  return <div className="listing-chart-legend" aria-label="Grafik serileri hakkında bilgi">
    <LegendItem
      color="#2563eb"
      label="Tüm ilanlar"
      detail="Seçili filtreye uyan temizlenmiş ilanların fiyat görünümüdür."
    />
    {showClean && <LegendItem
      color="#16875b"
      label="Temiz araç ilanları"
      detail="İlan başlığı veya filtre bilgisinde boyasız, değişensiz ya da tramersiz beyanı bulunan ilanlardır. Ekspertiz doğrulaması değildir."
    />}
  </div>;
}
