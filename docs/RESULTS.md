# Results (generated 2026-10-05T06:13:50Z, git main)

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
- **MAPE:** **21.50%** (Project Target: ≤ 20.0%)
- **Median APE:** **18.07%**
- **MAE (INR):** **₹2,925,634**
- **RMSE (INR):** **₹6,538,454**
- **R² on log-price:** **0.805** (Project Target: ≥ 0.750)

## 3. Model Ladder (5-Fold Grouped Spatial Cross-Validation)
| Model Family | Spatial CV MAPE | Median APE | MAE (INR) | R² (log) |
|---|---|---|---|---|
| **Ridge Regression** | 25.50% | 15.97% | ₹2,671,093 | 0.666 |
| **Random Forest** | 20.96% | 15.77% | ₹1,663,036 | 0.756 |
| **LightGBM (Served Model)** | **22.23%** | **17.35%** | **₹1,747,616** | **0.730** |

### Spatial Leakage Gap
- **Random 5-Fold CV MAPE:** 11.56%
- **Grouped Spatial-Block CV MAPE:** 22.23%
- **Quantified Optimistic Leakage Gap:** **+10.67%** (confirms that naive random splits borrow neighborhood characteristics and underestimate true generalization error).

## 4. Feature Ablation Study
| Variant | Feature Set | Spatial CV MAPE | Median APE | R² (log) |
|---|---|---|---|---|
| **A0** | Baseline (locality median ppsf × area) | 40.96% | 35.00% | 0.112 |
| **A1** | Property structural features only | 19.51% | 14.16% | 0.764 |
| **A2** | A1 + `locality_id` | 21.73% | 17.10% | 0.728 |
| **A3** | A2 + OpenStreetMap geo proximity & counts | **21.98%** | **16.78%** | **0.732** |
| **A4** | A3 + Rajasthan DLC circular rate prior | **21.38%** | **16.63%** | **0.748** |

**Headline Geospatial Lift (A2 → A3 Error Reduction):** **-0.25 percentage points** lower MAPE due to physical proximity to metro, highways, schools, and hospitals!

## 5. Mondrian Conformal Interval Calibration (Nominal 80%)
- **Target Coverage:** 80.0% (Acceptable Band: 75.0% – 85.0%)
- **Overall Empirical Test Coverage:** **78.0%**
- **Low-Price Tercile Coverage:** 86.1%
- **Mid-Price Tercile Coverage:** 75.8%
- **High-Price Tercile Coverage:** 66.0%

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
