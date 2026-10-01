# Data Dictionary: Canonical Schema & Feature Specifications

**Version:** 1.0.0  
**Updated:** 2026-09-30  
**Status:** Canonical  

---

## 1. Canonical Listing Table Schema (`data/interim/listings_std.parquet`)

| Field Name | Data Type | Nullable | Description & Domain Values | Unit / Format | Source Origin |
|---|---|---|---|---|---|
| `listing_id` | `string` | No | Stable SHA-256 hash of `source + ":" + original_row_id` | 16-char hex | Derived |
| `source` | `category` | No | Dataset name: `karanveer_jaipur`, `anmolkumar` | string | Ingest |
| `price_inr` | `float64` | No | Asking price in Indian Rupees (Target variable) | ₹ (INR) | Normalized |
| `area_sqft` | `float64` | No | Total covered/built-up area | Square feet | Normalized |
| `area_type` | `category` | Yes | Carpet / Built-up / Super Built-up / Unknown | category | `karanveer_jaipur` |
| `bhk` | `int64` | No | Number of bedrooms (RK mapped to 1) | count | Normalized |
| `bathrooms` | `Int64` | Yes | Number of bathrooms / washrooms | count | `karanveer_jaipur` |
| `property_type` | `category` | No | `apartment`, `independent_house`, `villa`, `builder_floor`, `other` | category | Ingest |
| `locality_raw` | `string` | No | Raw locality text extracted from source | text | Ingest |
| `locality_id` | `string` | Yes | Standardized locality slug (populated in Phase 3) | snake_case | Locality normalization |
| `lat` | `float64` | Yes | WGS84 Latitude degree (26.0° to 28.0°) | degrees N | Coordinates |
| `lon` | `float64` | Yes | WGS84 Longitude degree (75.0° to 77.0°) | degrees E | Coordinates |
| `coord_precision` | `category` | No | Coordinate precision level: `exact`, `locality_centroid`, `missing` | category | Coordinates |
| `age_years` | `float64` | Yes | Property age in years | years | Ingest |
| `floor` | `Int64` | Yes | Floor number of the listing | integer | Ingest |
| `total_floors` | `Int64` | Yes | Total floors in the building/society | integer | Ingest |
| `furnishing` | `category` | Yes | `unfurnished`, `semi_furnished`, `furnished`, `unknown` | category | Ingest |
| `possession_status` | `category` | Yes | `ready_to_move`, `under_construction`, `unknown` | category | Ingest |
| `posted_by` | `category` | Yes | `owner`, `dealer`, `builder`, `unknown` (NEVER a personal name) | category | Ingest |
| `rera_flag` | `boolean` | Yes | RERA approved project indicator (True/False/None) | bool | Ingest |
| `listing_date` | `date` | Yes | Date listing was posted/scraped | YYYY-MM-DD | Ingest |

---

## 2. Personal Data Protection Policy

In strict accordance with Ground Rules B7:
- **Zero Personally Identifiable Information (PII):** Owner names, dealer contact names, telephone numbers, email addresses, and house/door/flat numbers are stripped at ingestion.
- The `posted_by` column is strictly constrained to the categorical role (`owner`, `dealer`, `builder`).
- Listing URLs from scrapers (e.g. `property_link` in `karanveer_jaipur`) are completely dropped.

---

## 3. Geospatial Feature Columns (Engineered in Phase 4)

| Feature Name | Feature Group | Type | Description |
|---|---|---|---|
| `dist_metro_m` | Connectivity | float | Distance to nearest Jaipur Metro station (meters) |
| `dist_rail_m` | Connectivity | float | Distance to nearest railway station (meters) |
| `dist_airport_m` | Connectivity | float | Distance to Jaipur International Airport (meters) |
| `dist_primary_road_m` | Connectivity | float | Distance to nearest primary/trunk/secondary highway (meters) |
| `dist_cbd_m` | Connectivity | float | Distance to Jaipur central commercial hub (meters) |
| `dist_hospital_m` | Neighbourhood amenities | float | Distance to nearest hospital / health clinic (meters) |
| `dist_school_m` | Neighbourhood amenities | float | Distance to nearest school / college (meters) |
| `dist_mall_m` | Neighbourhood amenities | float | Distance to nearest shopping mall / commercial center (meters) |
| `dist_park_m` | Neighbourhood amenities | float | Distance to nearest public park or garden (meters) |
| `n_school_1000m` | Neighbourhood amenities | int | Count of schools within 1 km radius |
| `n_hospital_1000m` | Neighbourhood amenities | int | Count of hospitals within 1 km radius |
| `n_restaurant_1000m` | Neighbourhood amenities | int | Count of restaurants/cafes within 1 km radius |
| `n_shop_1000m` | Neighbourhood amenities | int | Count of retail shops/supermarkets within 1 km radius |
| `dlc_rate_per_sqm` | Locality & market | float | Rajasthan Government circle rate (₹/sq m) |
| `knn_log_ppsf_median` | Locality & market | float | Leakage-safe in-fold median log-price-per-sqft among k-nearest training listings |
