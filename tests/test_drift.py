"""Unit tests for Population Stability Index (PSI) and feature drift monitoring."""

import numpy as np
import pandas as pd
import pytest

from jpi.monitoring.drift import calculate_drift_report, calculate_psi


def test_psi_identical_distributions():
    """Identical distributions produce near-zero PSI."""
    np.random.seed(42)
    dist = np.random.normal(100, 15, 1000)
    psi = calculate_psi(dist, dist)
    assert psi < 0.01


def test_psi_shifted_distribution():
    """Substantially shifted distribution flags high PSI."""
    np.random.seed(42)
    dist_ref = np.random.normal(100, 15, 1000)
    dist_cur = np.random.normal(150, 15, 1000)
    psi = calculate_psi(dist_ref, dist_cur)
    assert psi > 0.25


def test_calculate_drift_report():
    """Drift report accurately evaluates DataFrame columns."""
    df_ref = pd.DataFrame(
        {
            "area": [1000, 1200, 1400, 1600, 1800] * 20,
            "bhk": [2, 2, 3, 3, 4] * 20,
        }
    )
    df_cur = pd.DataFrame(
        {
            "area": [1000, 1200, 1400, 1600, 1800] * 20,
            "bhk": [2, 2, 3, 3, 4] * 20,
        }
    )

    report = calculate_drift_report(df_ref, df_cur, ["area", "bhk"])
    assert report["status"] == "PASS"
    assert report["features_audited"] == 2
    assert report["features_flagged"] == 0
    assert report["metrics"]["area"]["status"] == "STABLE"
