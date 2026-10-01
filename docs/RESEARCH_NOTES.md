# Research Notes: Hedonic House Price Modeling, Spatial CV, and Conformal Prediction

**Date:** 2026-09-30  
**Author:** Executor  
**Task:** R5 — Prior-Art Review  

---

## 1. Key Literature & Prior Art

### A. Hedonic House Price Modeling
- **Foundational Work:** Rosen, S. (1974). *Hedonic Prices and Implicit Markets: Product Differentiation in Pure Competition*. JPE.
- **Modern Machine Learning Practice:** Gradient boosted trees (LightGBM, XGBoost) consistently outperform OLS and spatial autoregressive models (SAR/SEM) on real estate tabular benchmarks, achieving 15%–25% MAPE on Indian and international housing datasets.
- **Feature Architecture:** Structural features (area, BHK, age, floor ratio) capture baseline utility, while spatial proximity (distances to transit, CBD, amenities) and neighborhood density capture accessibility premiums.

### B. Spatial Cross-Validation vs. Random Splits
- **Key Reference:** Roberts, D. R. et al. (2017). *Cross-validation strategies for data with temporal, spatial, or phylogenetic structure*. Ecography, 40(8), 913-929.
- **Valavi, R. et al. (2019):** *blockCV: An R package for generating spatially or environmentally separated folds*. Methods in Ecology and Evolution.
- **The Pitfall (Spatial Leakage):** Standard random k-fold cross-validation suffers severe optimistic bias in geospatial applications. Because nearby properties share unobserved spatial characteristics (road quality, developer reputation, water availability, noise), random splits allow validation instances to borrow information from immediate neighbors in the training set. This can artificially depress reported MAPE by 5–10 percentage points (e.g., 12% random vs 20% spatial).
- **Our Approach:** Spatially disjoint block partitioning (`GroupKFold` on ~2.2 km lat/lon blocks, `SPATIAL_BLOCK_DEG = 0.02`). Final test set is strictly block-isolated. Both random-split and spatial-split errors will be measured and compared to quantify the leakage gap.

### C. Conformal Prediction for Tabular Regression
- **Key Reference:** Vovk, V. et al. (2005). *Algorithmic Learning in a Random World*. Springer; Angelopoulos, A. N., & Bates, S. (2021). *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*.
- **Mechanism:** Using out-of-fold residuals $|y_i - \hat{y}_i|$ from spatial CV, compute the finite-sample nonconformity quantile:
  $$q = \text{Quantile}\left(|e|, \frac{\lceil (n+1)(1-\alpha) \rceil}{n}\right)$$
  Yielding distribution-free coverage guarantee: $P(y \in [\hat{y} - q, \hat{y} + q]) \ge 1 - \alpha$.
- **Refinement:** Mondrian conformal prediction evaluates separate halfwidths per predicted price tercile (low, mid, high) to account for heteroskedasticity.

### D. Tree SHAP and Native Exact Multiplicative Effects
- **Key Reference:** Lundberg, S. M. et al. (2020). *From local explanations to global understanding with explainable AI for trees*. Nature Machine Intelligence.
- **The Log-Space Multiplicative Invariant:** When $y = \ln(\text{price})$, LightGBM's native tree contribution decomposes the prediction additively:
  $$\ln(\hat{y}) = \text{base} + \sum_{i=1}^m c_i$$
  Exponentiating yields an exact multiplicative factor decomposition:
  $$\hat{y} = e^{\text{base}} \times \prod_{i=1}^m e^{c_i}$$
  The individual factor impact is exactly $(e^{c_i} - 1) \times 100\%$.
- **The Serving Pitfall:** Importing the Python `shap` package in production pulls massive dependencies (numba, llvmlite, scipy, matplotlib) and bloats memory beyond 500 MB.
- **Our Innovation:** In production, we call LightGBM's native C++ implementation `booster.predict(X, pred_contrib=True)`. It computes the exact TreeSHAP values in < 5 ms with zero extra libraries.

---

## 2. Benchmark Error Ranges & Targets

| Benchmark Metric | Literature Standard (India Housing) | Our Target (Section B6) |
|---|---|---|
| Random Split MAPE | 10% – 16% | Evaluated only for comparison |
| Spatial CV MAPE | 18% – 26% | **≤ 20%** (Stretch: ≤ 15%) |
| Median APE | 12% – 18% | Reported alongside MAPE |
| $R^2$ on $\ln(\text{price})$ | 0.70 – 0.82 | **≥ 0.75** |
| 80% Interval Coverage | Often uncalibrated (60%–70%) | **75% – 85%** (calibrated) |

---

## 3. What We Will Do Differently

1. **Zero Database Serving:** Everything precomputed and serialized into lean static artifacts (`model.txt`, `geo_layers.npz`, JSON stats). Fits a 512 MB free container.
2. **Native LightGBM Contributions:** No `shap` package in the production image. Multiplicative factors are exact, not approximations.
3. **Mondrian Conformal Calibration:** Guaranteed 80% intervals split by price tier, verified on an untouched spatial test block.
4. **Leakage-Isolated Nearest Index:** Shared `NearestIndex` class for training and serving, with automated CI parity tests ensuring zero train-serving skew.
