# Data & Feature Drift Audit

**Audit Status:** `ALERT_RETRAIN_REQUIRED`  
**Features Audited:** 7 | **Flagged Drift:** 6

### Population Stability Index (PSI) Thresholds:
- **PSI < 0.10:** Stable (no significant distribution change)
- **0.10 ≤ PSI < 0.25:** Moderate drift (monitor closely)
- **PSI ≥ 0.25:** Significant drift (triggers automatic retraining)

| Feature | PSI Score | Status | Train Reference Mean | Test Sample Mean |
|---|---|---|---|---|
| `area_sqft` | 0.3187 | `SIGNIFICANT_DRIFT` | 1275.7 | 1408.0 |
| `bhk` | 0.1008 | `MODERATE_DRIFT` | 2.4 | 2.7 |
| `dist_metro_m` | 5.2928 | `SIGNIFICANT_DRIFT` | 3799.0 | 5203.5 |
| `dist_cbd_m` | 4.4496 | `SIGNIFICANT_DRIFT` | 3298.9 | 3967.8 |
| `dist_primary_road_m` | 1.0786 | `SIGNIFICANT_DRIFT` | 1099.7 | 2919.0 |
| `dlc_rate_per_sqm` | 5.0020 | `SIGNIFICANT_DRIFT` | 33845.2 | 32522.0 |
| `log_price` | 0.2937 | `SIGNIFICANT_DRIFT` | 15.5 | 15.5 |
