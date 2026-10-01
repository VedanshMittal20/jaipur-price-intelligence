# Data Cleaning & Validation Report (Phase 3)

**Report Date:** 2026-10-01  
**Author:** Executor  
**Input:** `data/interim/listings_std.parquet` (3,453 rows)  
**Output:** `data/processed/listings_clean.parquet` (2,510 rows)  

---

## 1. Data Cleaning Waterfall

| Stage / Operation | Starting Rows | Rows Dropped | Resulting Rows | Rationale & Method |
|---|---|---|---|---|
| **1. Standardized Ingest** | 3,453 | 0 | 3,453 | Merged `karanveer_jaipur` (2,490) and `anmolkumar` (963) with valid `price > 0` and `area > 0`. |
| **2. Exact Deduplication** | 3,453 | **342** | 3,111 | Dropped exact duplicate listings matching on `[source, price_inr, area_sqft, bhk, locality_raw]`. |
| **3. Near Deduplication** | 3,111 | **478** | 2,633 | Dropped duplicate aggregator listings within same locality having rounded area (±10 sqft) and price (±₹50k). |
| **4. Outlier & Bounds Filtering** | 2,633 | **123** | **2,510** | Filtered hard bounds (`area_sqft` outside [200, 20,000], `bhk` outside [1, 10], `ppsf` outside [1,000, 30,000]) and locality group robust z-scores ($|z| > 3.5$). |
| **Final Clean Output** | — | — | **2,510** | Validated against Pandera schema contract. |

**Waterfall Arithmetic Check:** $3,453 - (342 + 478 + 123) = 3,453 - 943 = 2,510$ (100% exact reconciliation).

---

## 2. Key Profiling Observations (Task C1)

1. **Locality Resolution:** 91.55% of listings successfully resolve to standardized canonical localities (exceeds the ≥ 90% project threshold).
2. **Duplicate Density:** SquareYards aggregator listings had significant near-duplicate density (different broker IDs posting the same unit in societies like *Mahima Sansaar* and *Shree Govind Crystal City*). Deduplication eliminated 820 redundant entries.
3. **Price Discrepancies:** A minority of listings in `anmolkumar` had price entered in Crores without label, or recorded monthly rent instead of purchase price (e.g., PPSF < ₹500/sqft). These were flagged and filtered.
4. **Coordinate Accuracy:** In `anmolkumar`, original column headers `LATITUDE` and `LONGITUDE` were swapped. After inversion, 715 listings (100% of within-city rows) landed accurately in Jaipur.
5. **Locality Centroid Anchor:** All 1,795 listings from `karanveer_jaipur` were anchored to verified WGS84 centroids in `geocode_cache.json` with `coord_precision = locality_centroid`.

---

## 3. Missing Value Policy (Task C5)

| Field | Treatment in Pipeline | Rationale |
|---|---|---|
| `price_inr` (Target) | **Never imputed.** Any missing/non-positive row dropped at ingest. | Target integrity rule (B7). |
| `area_sqft`, `bhk` | **Never imputed.** Mandatory fields. Missing rows dropped. | Core structural drivers. |
| `bathrooms` | Nullable numeric. Left as NaN for LightGBM/XGBoost; median-imputed + `_missing` flag for linear models in pipeline. | Missing on 27.9% of rows. |
| `floor` | Nullable integer. Left as NaN for tree models. | Missing on 74.7% of rows. |
| `age_years`, `total_floors` | High missingness (>70%). Dropped from baseline model features; used as optional UI inputs. | Avoid sparse distortion. |
| Categoricals (`furnishing`, `possession_status`, `posted_by`) | Explicit `'unknown'` category level. | Avoid categorical drop. |

---

## 4. Locality Canonicalization (Task C3)

- **Mapping file committed:** `data/external/locality_map.csv`
- **Total distinct canonical localities:** 34 major micro-markets + 1 `other` category
- **Resolution rate:** **91.55%**
- **Top localities by volume:**
  - Ajmer Road: 285 listings
  - Mansarovar: 283 listings
  - Jagatpura: 220 listings
  - Girdharipura: 176 listings
  - Vaishali Nagar: 174 listings
  - Anand Nagar: 109 listings
  - Sirsi Road: 80 listings
  - Shyam Nagar: 78 listings
  - Gurjar Ki Thadi: 78 listings
