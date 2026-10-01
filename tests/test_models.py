"""Unit tests for conformal prediction and exact multiplicative factor explanations."""

import json
import math
import numpy as np
import pytest
import lightgbm as lgb

from jpi.config import ART
from jpi.models.conformal import MondrianConformalCalibrator, compute_conformal_halfwidth
from jpi.models.explain import explain_prediction


def test_conformal_calibrator_properties(tmp_path):
    """Calibrator produces monotonic intervals and round-trips via JSON."""
    np.random.seed(42)
    y_true_log = np.random.normal(16.0, 0.5, 100)
    y_pred_log = y_true_log + np.random.normal(0, 0.1, 100)

    cal = MondrianConformalCalibrator(alpha=0.20)
    cal.fit(y_true_log, y_pred_log)

    assert len(cal.tercile_edges) == 2
    assert len(cal.tercile_halfwidths) == 3
    assert cal.global_halfwidth > 0

    # Interval test for three points
    test_points = [15.0, 16.0, 17.5]
    for pt in test_points:
        lo, mid, hi = cal.predict_interval(pt)
        assert lo < mid < hi
        assert math.isclose(mid, math.exp(pt), rel_tol=1e-5)

    # Save and reload
    save_file = tmp_path / "conformal.json"
    cal.save(save_file)
    loaded = MondrianConformalCalibrator.load(save_file)

    assert loaded.alpha == cal.alpha
    assert loaded.global_halfwidth == cal.global_halfwidth
    assert loaded.tercile_edges == cal.tercile_edges


def test_exact_multiplicative_parity():
    """Mathematical verification: typical_price * prod(exp(c_i)) == estimate_inr."""
    # Mock log contributions: [c0, c1, c2, c3, base]
    contrib_row = np.array([0.15, -0.08, 0.22, -0.05, 15.5])
    feature_names = ["area_sqft", "dist_metro_m", "bhk", "bathrooms"]
    groups = {
        "area_sqft": "Space",
        "dist_metro_m": "Connectivity",
        "bhk": "Space",
        "bathrooms": "Space",
    }
    labels = {f: f.upper() for f in feature_names}

    exp = explain_prediction(contrib_row, feature_names, groups, labels, top_k=4)

    base = contrib_row[-1]
    expected_typical = math.exp(base)
    expected_estimate = math.exp(base + np.sum(contrib_row[:-1]))

    assert math.isclose(exp["typical_price_inr"], expected_typical, rel_tol=1e-6)
    assert math.isclose(exp["estimate_inr"], expected_estimate, rel_tol=1e-6)

    # Multiplicative product of individual factors
    total_factor_product = 1.0
    for feat in exp["features"]:
        total_factor_product *= feat["factor"]

    reconstructed_estimate = exp["typical_price_inr"] * total_factor_product
    assert math.isclose(reconstructed_estimate, exp["estimate_inr"], rel_tol=1e-5)


def test_production_booster_exists_and_predicts():
    """Trained booster loads and returns realistic price predictions."""
    model_path = ART / "model" / "model.txt"
    assert model_path.exists(), "Production model.txt must exist"

    booster = lgb.Booster(model_file=str(model_path))
    assert booster.num_trees() > 0

    # Test dummy row of 35 features
    dummy_x = np.ones((1, booster.num_feature()))
    pred_log = booster.predict(dummy_x)
    pred_inr = math.exp(pred_log[0])

    # Realistic Jaipur residential price range: ₹5 Lakh to ₹50 Crore
    assert 500_000 <= pred_inr <= 500_000_000
