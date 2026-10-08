# Original User Request

## Initial Request — 2026-10-01T06:52:11Z

Modernize the Jaipur Price Intelligence Platform by upgrading the interactive map to high-resolution retina cartographic tiles and recalibrating the price valuation engine to 2026 market values using official Jaipur RBI Housing Price Index (HPI) curves and recent Rajasthan DLC circle rate revisions.

Working directory: c:\Users\vedan\Documents\antigravity\clever-hubble
Integrity mode: development

## Requirements

### R1. Modern Cartographic Basemaps
Upgrade the Leaflet interactive map with crisp, modern CartoDB Positron / Voyager raster tiles with retina support, sub-second pan/zoom performance, and custom color-coded micro-market circle markers.

### R2. Temporal RBI HPI & 2026 Circle Rate Recalibration
Implement an inflation & appreciation recalibration pipeline based on official Reserve Bank of India (RBI) Jaipur Housing Price Index (HPI) series, adjusting historical listing prices to current 2026 market equivalents while reconciling statutory Rajasthan DLC rate floors.

### R3. Model Retraining & Spatial Validation
Retrain the LightGBM gradient boosted tree model on the 2026-calibrated dataset using strict 5-fold grouped spatial block cross-validation. Recalibrate Mondrian conformal prediction intervals (80% nominal coverage) and regenerate exact multiplicative TreeSHAP factor attributions.

### R4. Lean Serving & Full-Stack Parity
Update artifacts/ binaries (model.txt, preprocess.joblib, conformal.json), rebuild the static React web application, and verify end-to-end latency (< 50 ms) and container memory footprint (< 400 MB).

## Verification Resources
- Test suite: pytest -q tests (all unit, integration, parity, and leakage tests)
- End-to-end smoke benchmark: python scripts/smoke_test.py
- Browser validation: Chrome DevTools visual snapshot & headless rendering

## Acceptance Criteria

### Visual & Cartographic Modernization
- [ ] Map renders crisp high-res CartoDB tiles with zero 404 tile errors or rendering glitches
- [ ] Selected micro-market centroid markers, popups, and insight drawers display smoothly

### Data & Model Performance Guardrails
- [ ] Documented RBI HPI temporal adjustment formula and updated 2026 baseline prices
- [ ] Holdout Spatial Block R² >= 0.750
- [ ] Test Set Spatial MAPE <= 26.0%
- [ ] Calibrated Mondrian Conformal Interval empirical coverage >= 70.0% (nominal 80%)

### Production & Lean Serving Guardrails
- [ ] All 30+ tests in tests/ pass with zero failures
- [ ] Single-row /predict inference latency <= 50 ms
- [ ] Single-process RSS memory consumption remains <= 350 MB

## Follow-up Directive — 2026-10-01T06:53:34Z

User directive authorized: You and all spawned subagents (including orchestrators, implementers, and reviewers) have full authorization to use the 'pro' model tier (e.g. Gemini 3.1 Pro / Pro) for all reasoning, complex code generation, retraining, and verification passes. Ensure high-capability reasoning is leveraged wherever needed.
