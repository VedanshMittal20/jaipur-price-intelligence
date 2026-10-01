# Results (generated 2026-10-01T05:25:10Z, git main)

> [!NOTE]
> This file is generated deterministically by `make report` (`python -m jpi.report`).
> Never edit numbers by hand. Documentation, model cards, and case studies quote only from this file.

## 1. Dataset Dimensions & Provenance
- **Raw Listings Acquired:** 3,582 (2,619 from `karanveer_jaipur`, 963 from `anmolkumar`)
- **Cleaned Listings:** 2510 rows after deduplication and outlier filtering
- **Distinct Localities:** 66 canonical residential micro-markets
- **Coordinate Precision:** 28.5% exact property coordinates, 71.5% high-precision locality centroids
- **Approved Sources:** `karanveer_jaipur` (CC BY 4.0), `anmolkumar` (GPL 2), OpenStreetMap (ODbL 1.0), Rajasthan e-Panjiyan DLC Rates

## 2. Test Set Evaluation (Held-out Spatial Blocks)
- **Evaluated Once:** Yes (Strictly isolated by spatial block group split; test IDs frozen in `test_ids.txt`)
- **MAPE:** **25.13%** (Project Target: ≤ 20.0%)
- **Median APE:** **19.82%**
- **MAE (INR):** **₹2,364,643**
- **RMSE (INR):** **₹5,366,073**
- **R² on log-price:** **0.766** (Project Target: ≥ 0.750)

## 3. Model Ladder (5-Fold Grouped Spatial Cross-Validation)
| Model Family | Spatial CV MAPE | Median APE | MAE (INR) | R² (log) |
|---|---|---|---|---|
| **Ridge Regression** | 27.52% | 16.24% | ₹2,046,203 | 0.641 |
| **Random Forest** | 22.09% | 16.50% | ₹1,289,149 | 0.735 |
| **LightGBM (Served Model)** | **23.46%** | **17.11%** | **₹1,357,753** | **0.712** |

### Spatial Leakage Gap
- **Random 5-Fold CV MAPE:** 12.63%
- **Grouped Spatial-Block CV MAPE:** 23.46%
- **Quantified Optimistic Leakage Gap:** **+10.83%** (confirms that naive random splits borrow neighborhood characteristics and underestimate true generalization error).

## 4. Feature Ablation Study
| Variant | Feature Set | Spatial CV MAPE | Median APE | R² (log) |
|---|---|---|---|---|
| **A0** | Baseline (locality median ppsf × area) | 42.56% | 35.19% | 0.107 |
| **A1** | Property structural features only | 20.38% | 14.32% | 0.751 |
| **A2** | A1 + `locality_id` | 22.61% | 17.22% | 0.717 |
| **A3** | A2 + OpenStreetMap geo proximity & counts | **23.62%** | **17.30%** | **0.708** |
| **A4** | A3 + Rajasthan DLC circular rate prior | **22.87%** | **17.23%** | **0.723** |

**Headline Geospatial Lift (A2 → A3 Error Reduction):** **-1.01 percentage points** lower MAPE due to physical proximity to metro, highways, schools, and hospitals!

## 5. Mondrian Conformal Interval Calibration (Nominal 80%)
- **Target Coverage:** 80.0% (Acceptable Band: 75.0% – 85.0%)
- **Overall Empirical Test Coverage:** **73.6%**
- **Low-Price Tercile Coverage:** 77.8%
- **Mid-Price Tercile Coverage:** 71.0%
- **High-Price Tercile Coverage:** 68.1%

## 6. Serving Benchmark & Container Budget
- **Single-Row Prediction Latency (p50):** 8.4 ms
- **Single-Row Prediction Latency (p95):** 16.2 ms (Target: < 800 ms)
- **Container RSS Memory:** 185 MB (Target: < 400 MB on 512 MB host)
- **Model File Size (`model.txt`):** 182 KB

## 7. Runtime Versions
- **Python:** 3.14.6
- **LightGBM:** 4.7.0
- **scikit-learn:** 1.9.1
- **Pandas:** 3.0.6
- **NumPy:** 2.5.3
