export type Filters = {
  brand?: string;
  series?: string;
  model?: string;
  body_type?: string;
  fuel_type?: string;
  transmission?: string;
  year_min?: number;
  year_max?: number;
  mileage_max?: number;
};

export type CatalogOption = { name: string; listing_count?: number | null };
export type CatalogResponse = { items: CatalogOption[] };

export type MarketOverview = {
  median_price: number | null;
  average_price: number | null;
  listing_count: number;
  last_updated_at: string | null;
  source_status: string;
  change_30d: number | null;
  change_90d: number | null;
  change_yoy: number | null;
  message?: string | null;
};

export type TrendPoint = {
  date: string;
  median_price: number;
  average_price: number;
  listing_count: number;
};
export type TrendResponse = { available: boolean; label: string; points: TrendPoint[]; message?: string | null };

export type MarketTableRow = {
  label: string;
  average_price: number;
  median_price: number;
  listing_count: number;
  change_30d: number | null;
  change_90d: number | null;
  change_yoy: number | null;
};
export type MarketTableResponse = { group_by: string; rows: MarketTableRow[]; message?: string | null };

export type MoverItem = {
  label: string;
  change_percent: number;
  average_price: number;
  listing_count: number;
  direction: "up" | "down";
};
export type MoversResponse = { available: boolean; items: MoverItem[]; message?: string | null };

export type SimilarListing = {
  id: number | null;
  title: string;
  brand: string | null;
  series: string | null;
  model: string | null;
  year: number | null;
  mileage_km: number | null;
  price: number;
  city: string | null;
  listing_date: string | null;
  listing_url: string | null;
  similarity_score: number | null;
};

export type ValuationRequest = Filters & { year?: number; mileage_km?: number; asking_price?: number };
export type ValuationResponse = {
  status: string;
  estimated_market_value: number | null;
  recommended_low_price: number | null;
  recommended_high_price: number | null;
  median_price: number | null;
  listing_count: number;
  confidence: string | null;
  price_assessment: string | null;
  asking_price_delta_percent: number | null;
  explanation: string;
  similar_listings: SimilarListing[];
};
