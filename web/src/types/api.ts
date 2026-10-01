/** TypeScript definitions matching the backend FastAPI schemas */

export interface PropertyRequest {
  area_sqft: number;
  bhk: number;
  bathrooms?: number;
  floor?: number;
  total_floors?: number;
  property_type: string;
  furnishing: string;
  possession_status: string;
  posted_by: string;
  rera_flag: number;
  locality?: string;
  lat?: number;
  lon?: number;
}

export interface FeatureFactor {
  feature: string;
  label: string;
  factor: number;
  effect_pct: number;
  direction: 'positive' | 'negative';
}

export interface GroupFactor {
  group: string;
  factor: number;
  effect_pct: number;
  direction: 'positive' | 'negative';
}

export interface PricePredictionResponse {
  estimate_inr: number;
  estimate_ppsf: number;
  interval_low_inr: number;
  interval_high_inr: number;
  interval_low_ppsf: number;
  interval_high_ppsf: number;
  nominal_coverage: number;
  typical_price_inr: number;
  locality: string;
  lat: number;
  lon: number;
  coord_precision: string;
  dlc_rate_per_sqm?: number | null;
  factors: FeatureFactor[];
  groups: GroupFactor[];
}

export interface LocalitySummary {
  locality_id: string;
  name: string;
  lat: number;
  lon: number;
  median_price_inr: number;
  median_ppsf: number;
  listing_count: number;
  dlc_rate_per_sqm?: number | null;
  dist_metro_km?: number | null;
}

export interface DealSummary {
  listing_id: string;
  locality: string;
  bhk: number;
  area_sqft: number;
  actual_price_inr: number;
  actual_ppsf: number;
  predicted_price_inr: number;
  predicted_ppsf: number;
  discount_pct: number;
  lat: number;
  lon: number;
}

export interface ModelMetaResponse {
  model_name: string;
  model_version: string;
  trained_at: string;
  features_count: number;
  spatial_cv_mape: number;
  test_mape: number;
  test_r2: number;
  nominal_coverage: number;
  empirical_coverage: number;
  container_ram_budget: string;
}
