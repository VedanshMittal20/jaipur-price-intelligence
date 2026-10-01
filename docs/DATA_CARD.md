# Data Card: Jaipur Real Estate Listing & Geospatial Intelligence Dataset

**Dataset Version:** 1.0.0  
**Date:** 2026-09-30  
**Curators:** Vedansh, Jaipur Price Intelligence Platform Contributors  

---

## 1. Dataset Overview & Intended Use

- **Primary Goal:** Train a machine learning hedonic pricing model for residential properties in Jaipur, Rajasthan, and provide localized uncertainty bounds and exact multiplicative factor explanations.
- **Intended Use:** Educational and analytical portfolio project, pricing guidance, and market transparency research.
- **Out-of-Scope Use:** Not a government-certified property valuation. Must not be used as official assessment for bank lending, taxation, court appraisal, or title transactions.

---

## 2. Dataset Provenance & Licences

| Source Identifier | Dataset Title | Contributor / Publisher | Origin URL | Licence |
|---|---|---|---|---|
| `karanveer_jaipur` | Real Estate Property Dataset | Karan Veer (`karanveer59`) | [Kaggle Dataset](https://www.kaggle.com/datasets/karanveer59/real-estate-property-dataset) | **Attribution 4.0 International (CC BY 4.0)** |
| `anmolkumar` | House Price Prediction Challenge | Anmol Kumar / Devrup Banerjee | [Kaggle Dataset](https://www.kaggle.com/datasets/anmolkumar/house-price-prediction-challenge) | **GNU General Public License v2.0 (GPL 2)** |
| `osm_jaipur` | OpenStreetMap Jaipur Spatial Layers | OpenStreetMap contributors | [OpenStreetMap](https://www.openstreetmap.org/) | **Open Database License (ODbL 1.0)** |
| `rajasthan_dlc` | Official Rajasthan DLC Rates | Government of Rajasthan (e-Panjiyan) | [e-Panjiyan Portal](https://epanjiyan.rajasthan.gov.in/) | **State Public Valuation Circulars** |

---

## 3. Data Collection & Preprocessing Methodology

1. **Ingestion:** Raw CSVs downloaded from approved sources with verified SHA-256 checksums.
2. **PII Removal:** All personal names, phone numbers, email addresses, and specific flat/door numbers are stripped at ingestion.
3. **Coordinate Standardization:** Geocoding is anchored to locality centroids for scraper listings, while provided coordinates from `anmolkumar` are verified and corrected for a known latitude/longitude column swap.
4. **Locality Resolution:** Standardized via documented rule-based mappings (`data/external/locality_map.csv`).

---

## 4. Known Biases & Limitations

1. **Asking Price vs. Transaction Price:** Real estate listings represent seller *asking* prices. Final deed registry prices typically carry a 5% to 15% negotiation discount.
2. **Online Portal Selection Bias:** Listings sourced from online aggregators skew towards modern apartment societies, new developments, and institutional builder inventory, under-representing ancestral properties in the historic Walled City.
3. **Temporal Spread:** Datasets span 2020 through 2026. General inflation and metro corridor expansion have created price appreciation over this window.
4. **Coordinate Precision:** Listings geocoded to locality centroids do not capture micro-street noise or facing variations. The model explicitly records `coord_precision = locality_centroid` for transparency.
