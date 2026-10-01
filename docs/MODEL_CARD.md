# Model Card — Jaipur Residential Price Intelligence Booster

## Model Details
- **Developer:** Vedansh (B.E. CSE, Data Science)
- **Model Date:** October 2026
- **Model Version:** 2.0.0
- **Model Type:** Gradient Boosted Decision Trees (`lightgbm.Booster`)
- **Target Variable:** Natural log of asking price: $y = \ln(\text{price\_inr})$
- **Inference Mode:** Point prediction ($\exp(\hat{y})$) + Mondrian Conformal Prediction 80% intervals + Native TreeSHAP multiplicative factor attribution (`pred_contrib=True`).
- **License:** MIT License

## Intended Use
- **Primary Intended Uses:**
  - Fair asking price estimation for residential flats, builder floors, and villas in Jaipur, Rajasthan.
  - Transparent per-factor value attribution for home buyers, sellers, and property brokers.
  - Identification of underpriced residential market listings (arbitrage deal detection).
- **Out-of-Scope Uses:**
  - Statutory or legal property valuation under Section 34AB of the Wealth Tax Act or Rajasthan Stamp Act.
  - Commercial properties, office spaces, retail malls, or agricultural land.
  - Financial underwriting or mortgage collateral clearance without physical inspection.

## Training Data & Provenance
- **Dataset Dimensions:** 2,510 cleaned listings across 66 canonical residential micro-markets in Greater Jaipur.
- **Approved Sources:**
  - `karanveer_jaipur` (CC BY 4.0): 2,619 raw listings.
  - `anmolkumar` (GPL 2): 963 raw listings.
  - OpenStreetMap (ODbL 1.0): 11 feature layers (metro, railway, airport, roads, schools, hospitals, parks, commercial shops).
  - Rajasthan e-Panjiyan / IGRS portal: statutory DLC circle rates (₹/sqm) across 34 colony clusters.
- **Data Filtering:**
  - Exact deduplication: 342 duplicates removed.
  - Near deduplication: 478 listings with identical coordinates, BHK, and price removed.
  - Outlier filtering: 123 listings outside physical boundaries (PPSF < ₹1,000 or > ₹30,000, Area < 200 sq ft or > 20,000 sq ft) removed.
  - PII Sanitization: 100% of broker/owner names, phone numbers, and street addresses stripped at ingestion.

## Evaluation & Metrics
All metrics are verified from held-out spatial blocks evaluated once (`docs/RESULTS.md`):

### 1. Test Set Performance (Held-out Spatial Blocks)
- **MAPE:** **25.13%** (Target: &le; 20.0%)
- **Median APE:** **19.82%**
- **MAE:** **₹2,364,643**
- **RMSE:** **₹5,366,073**
- **R² on log-price:** **0.766** (Target: &ge; 0.750 ✓)

### 2. Cross-Validation Ladder (5-Fold Grouped Spatial CV)
| Model Architecture | Spatial CV MAPE | Median APE | MAE (INR) | R² (log) |
|---|---|---|---|---|
| Baseline A0 (Locality Median) | 42.56% | 35.19% | ₹2,840,110 | 0.107 |
| Ridge Regression | 27.52% | 16.24% | ₹2,046,203 | 0.641 |
| Random Forest | 22.09% | 16.50% | ₹1,289,149 | 0.735 |
| **LightGBM (Served Booster)** | **23.46%** | **17.11%** | **₹1,357,753** | **0.712** |

### 3. Spatial Leakage Gap
- **Random 5-Fold CV MAPE:** 12.63%
- **Grouped Spatial-Block CV MAPE:** 23.46%
- **Optimistic Leakage Gap:** **+10.83%** (Quantifies the magnitude of false optimism from standard random splitting).

### 4. Conformal Interval Calibration (Nominal 80%)
- **Overall Empirical Coverage:** **73.6%**
- **Low-Price Tier Coverage:** 77.8%
- **Mid-Price Tier Coverage:** 71.0%
- **High-Price Tier Coverage:** 68.1%

## Ethical Considerations & Fairness
- **Geographic Bias:** Peripheral rural blocks with fewer than 3 listings have higher variance and fallback to locality median priors.
- **Privacy Protection:** No private personal contact numbers or names are persisted or utilized as features.
- **Explainability:** Zero "black box" decisions; every prediction returns exact positive and negative factors directly decomposed from tree split paths.
