# Engineering Case Study: Building a Leakage-Free Real Estate Valuation Platform

**Author:** Vedansh (B.E. CSE, Data Science)  
**Project:** Jaipur Real Estate Price Intelligence Platform  
**System Architecture:** FastAPI + LightGBM + React 18 / TypeScript / Leaflet  

---

## Executive Summary
Real estate valuation machine learning models routinely fail in production despite reporting 90%+ accuracy during training. This case study dissects the architectural flaws common in real estate AI systems, explains how we eliminated spatial autocorrelation leakage, derived exact multiplicative factor explanations without heavy dependencies, and packaged an end-to-end system within a 512 MB memory budget without an external database.

---

## 1. The Core Machine Learning Problem: Spatial Autocorrelation
Real estate listings exhibit strong spatial clustering (Tobler's First Law of Geography). When properties from the same apartment society or block are randomly partitioned into training and validation sets, random cross-validation yields a deceptively low **12.63% MAPE**.

### The Solution: Grouped Spatial Block Cross-Validation
We partitioned Greater Jaipur into a spatial grid ($\approx 2.2 \text{ km} \times 2.2 \text{ km}$ per block, `SPATIAL_BLOCK_DEG = 0.02`). Splitting folds strictly along spatial block boundaries revealed the honest out-of-sample generalization error: **23.46% MAPE**.

$$\text{Leakage Gap} = \text{Spatial CV MAPE} - \text{Random CV MAPE} = 23.46\% - 12.63\% = \mathbf{+10.83\%}$$

By acknowledging and engineering around this +10.83% leakage gap, our system prevents overfitting to specific micro-clusters and reliably estimates unobserved neighborhood developments.

---

## 2. Explainability Innovation: Native Multiplicative TreeSHAP
Property buyers and brokers do not accept black-box predictions. Standard explainability workflows import heavy libraries (`shap`, `matplotlib`, `scipy`) that inflate Docker container sizes beyond 2.5 GB and exhaust 512 MB free-tier RAM limits.

### The Mathematical Insight
Because the model predicts the natural logarithm of asking price ($y = \ln(\text{price})$), LightGBM's native tree contribution feature (`booster.predict(X, pred_contrib=True)`) computes exact additive contributions directly in log space:

$$\ln(\widehat{\text{Price}}) = \text{Base} + \sum_{i=1}^M c_i$$

Exponentiating both sides converts log-space additive contributions into exact multiplicative percentage factors:

$$\widehat{\text{Price}} = e^{\text{Base}} \cdot \prod_{i=1}^M e^{c_i} = \text{TypicalPrice} \cdot \prod_{i=1}^M (1 + \text{EffectPct}_i)$$

```
Mathematical Parity Check:
Typical Price:     ₹5,260,374
× Area Effect:     0.864 (-13.6%)
× Furnishing:      1.105 (+10.5%)
× Floor Factor:    0.929 (-7.1%)
...
= Estimated Price: ₹4,137,050 (Exact match to 1e-6 precision)
```

**Production Benefit:** Zero `shap` dependency in production, single-row explanation latency of **8.4 ms**, and 182 KB model weights.

---

## 3. Calibrated Uncertainty: Mondrian Conformal Prediction
Single point estimates in real estate are misleading. Standard regression standard errors rely on Gaussian residual assumptions that fail on skewed property distributions.

We implemented finite-sample **Mondrian Conformal Prediction** calibrated on out-of-fold cross-validation residuals. Non-conformity scores are computed conditionally across property price terciles (Budget, Mid-Tier, Luxury):

$$\mathcal{C}(x) = \left[ \exp(\hat{y} - \hat{q}_{k, 1-\alpha}), \; \exp(\hat{y} + \hat{q}_{k, 1-\alpha}) \right]$$

On the untouched held-out spatial test set, the empirical coverage reached **73.6%** against the nominal 80.0% guarantee.

---

## 4. Systems Architecture: The Lean-Serving Ladder
Most ML portfolio projects deploy heavy architectures: PostgreSQL + PostGIS + Redis + Celery + FastAPI + Docker. When hosted on free cloud tiers (Render, Hugging Face Spaces), free Postgres databases expire after 30 days and multi-container stacks run out of memory.

### Static-Artifact Serving (ADR-1 & ADR-3)
1. **Zero Database in Production:** All 66 micro-market aggregations, geocache centroids, and market arbitrage deals are pre-computed during CI and served from memory.
2. **Shared BallTree Haversine Index:** Both offline training and online serving use the identical `NearestIndex` implementation (`artifacts/geo/geo_layers.npz`), guaranteeing zero train-serve feature skew.
3. **Single Container Deployment:** The production Docker container serves the FastAPI backend and pre-built React/Tailwind/Leaflet static bundle from a single uvicorn worker, consuming just **185 MB RSS** (target: < 400 MB on 512 MB hosts).

---

## 5. Key Empirical Discoveries
1. **The Under-Construction Risk Discount:** Empirical analysis revealed a **17.1% discount** for under-construction properties versus ready-to-move counterparts in Jaipur, reflecting buyer liquidity and delay risk.
2. **Luxury Penalty Inversion:** While standard apartments exhibit diminishing price-per-square-foot returns as area increases, luxury apartments (> 1,800 sq ft) in C-Scheme and Civil Lines exhibit a positive correlation (+0.31), where larger floor plates command higher per-foot premiums.
3. **DLC Circle Rate Anchor:** Integrating Rajasthan e-Panjiyan statutory circle rates as an external feature provided a firm valuation floor, reducing median APE on high-value properties by 1.2 percentage points.

---

## 6. Conclusion
By pairing rigorous spatial machine learning methodologies with lean systems engineering, this platform provides reliable, interpretable, and reproducible real estate intelligence without cloud infrastructure overhead.
