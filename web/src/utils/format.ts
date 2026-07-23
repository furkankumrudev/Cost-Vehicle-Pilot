export const money = (value: number | null | undefined) =>
  value == null
    ? "Yeterli veri yok"
    : new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY", maximumFractionDigits: 0 }).format(value);

export const number = (value: number | null | undefined) =>
  value == null ? "—" : new Intl.NumberFormat("tr-TR").format(value);

export const percent = (value: number | null | undefined) =>
  value == null ? "—" : `${value > 0 ? "+" : ""}${new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1 }).format(value)}%`;

export const dateTime = (value: string | null | undefined) => {
  if (!value) return "Yeterli veri yok";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? value : new Intl.DateTimeFormat("tr-TR", { dateStyle: "medium", timeStyle: "short" }).format(parsed);
};

export const shortDate = (value: string) => new Intl.DateTimeFormat("tr-TR", { day: "numeric", month: "short" }).format(new Date(value));
