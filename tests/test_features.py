"""Tests for geospatial distance accuracy, nearest neighbor indexing, and leak checks."""

import numpy as np
import pandas as pd
import pytest

from jpi.config import ART, DATA
from jpi.geo.nearest import NearestIndex


def haversine_ground_truth(lat1, lon1, lat2, lon2):
    """Brute force Haversine distance in meters."""
    R = 6_371_000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


def test_nearest_index_accuracy():
    """Compare NearestIndex against brute-force haversine on 100 random pairs."""
    np.random.seed(42)
    targets = np.random.uniform([26.7, 75.6], [27.0, 76.0], size=(50, 2))
    queries = np.random.uniform([26.7, 75.6], [27.0, 76.0], size=(100, 2))

    idx = NearestIndex(targets)
    tree_dists = idx.nearest_m(queries)

    for i in range(len(queries)):
        q = queries[i]
        brute_dists = [haversine_ground_truth(q[0], q[1], t[0], t[1]) for t in targets]
        min_brute = min(brute_dists)
        assert abs(tree_dists[i] - min_brute) < 1.0, "Tree distance differs from brute force by > 1m!"


def test_nearest_index_k_nearest_m():
    """Verify k_nearest_m returns sorted top-k nearest distances."""
    np.random.seed(42)
    targets = np.random.uniform([26.7, 75.6], [27.0, 76.0], size=(30, 2))
    queries = np.random.uniform([26.7, 75.6], [27.0, 76.0], size=(10, 2))

    idx = NearestIndex(targets)
    k_dists = idx.k_nearest_m(queries, k=3)
    assert k_dists.shape == (10, 3)

    for i in range(len(queries)):
        q = queries[i]
        brute_sorted = sorted([haversine_ground_truth(q[0], q[1], t[0], t[1]) for t in targets])
        for rank in range(3):
            assert abs(k_dists[i, rank] - brute_sorted[rank]) < 1.0
        # Check ascending order
        assert k_dists[i, 0] <= k_dists[i, 1] <= k_dists[i, 2]


def test_nearest_index_with_index():
    """Verify nearest_with_index returns correct point indices."""
    np.random.seed(42)
    targets = np.array([
        [26.8500, 75.7600],
        [26.9000, 75.7800],
        [26.9500, 75.8000],
    ])
    idx = NearestIndex(targets)
    # Query very close to point 1
    query = np.array([26.9001, 75.7801])
    dists, indices = idx.nearest_with_index(query, k=1)
    assert indices[0, 0] == 1
    assert dists[0, 0] < 50.0  # within 50m


def test_nearest_index_validation():
    """Verify input validation on k bounds and invalid shapes."""
    targets = np.array([[26.85, 75.76], [26.90, 75.78]])
    idx = NearestIndex(targets)

    with pytest.raises(ValueError, match="k must be at least 1"):
        idx.k_nearest_m([[26.88, 75.77]], k=0)

    with pytest.raises(ValueError, match="exceeds indexed point count"):
        idx.k_nearest_m([[26.88, 75.77]], k=5)

    with pytest.raises(ValueError, match="need a non-empty"):
        NearestIndex(np.empty((0, 2)))


def test_leakage_audit_no_target_correlation():
    """Verify that no engineered input feature has correlation > 0.98 with log_price."""
    feats_path = DATA / "processed" / "features.parquet"
    df = pd.read_parquet(feats_path)
    target = df["log_price"]

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in ("price_inr", "log_price"):
            continue
        vals = df[col].fillna(0)
        if np.std(vals) < 1e-6:
            continue
        corr = np.corrcoef(vals, target)[0, 1]
        assert abs(corr) < 0.95, f"Leakage alert: feature '{col}' correlates {corr:.3f} with target!"


def test_hand_check_landmarks_table():
    """Hand-check distances to known Jaipur landmarks agree within tolerance."""
    z = np.load(ART / "geo" / "geo_layers.npz")
    metro_idx = NearestIndex(z["metro"])

    # 1. Civil Lines metro station entrance (lat: 26.9031, lon: 75.7871)
    d = metro_idx.nearest_m([[26.9031, 75.7871]])[0]
    assert d < 50.0  # within 50 meters of station point

    # 2. Statue Circle (26.9080, 75.8080) to nearest metro (Sindhi Camp / Civil Lines ~ 2-2.5 km)
    d_statue = metro_idx.nearest_m([[26.9080, 75.8080]])[0]
    assert 1500.0 < d_statue < 3000.0

    # 3. Mansarovar metro depot to Mansarovar station (~ 1 km)
    d_mansarovar = metro_idx.nearest_m([[26.8550, 75.7600]])[0]
    assert 500.0 < d_mansarovar < 1500.0


def test_knn_price_feature_no_self_leakage():
    """Verify that KNNPriceFeature does not leak a row's own price into its training transform."""
    from jpi.features.transformers import KNNPriceFeature

    df = pd.DataFrame(
        {
            "lat": [26.85, 26.86, 26.87, 26.88, 26.89, 26.90, 26.91, 26.92, 26.93, 26.94, 26.95, 26.96],
            "lon": [75.75, 75.76, 75.77, 75.78, 75.79, 75.80, 75.81, 75.82, 75.83, 75.84, 75.85, 75.86],
            "area_sqft": [1000.0] * 12,
        }
    )
    y1 = np.array([15.0] * 12)
    knn1 = KNNPriceFeature(k=3)
    res1 = knn1.fit_transform(df, y1)

    # Change only row 0's target price by 10x
    y2 = y1.copy()
    y2[0] = 25.0
    knn2 = KNNPriceFeature(k=3)
    res2 = knn2.fit_transform(df, y2)

    # Row 0's own feature MUST be unchanged because row 0 is excluded from its own neighbors!
    assert res1[0, 0] == pytest.approx(res2[0, 0], abs=1e-6)


def test_nearest_index_query_radius_distances():
    """Verify query_radius_distances returns correct sorted distances within threshold."""
    targets = np.array([
        [26.8500, 75.7600],
        [26.8520, 75.7620],
        [26.9500, 75.8000],  # far away (~11 km)
    ])
    idx = NearestIndex(targets)
    query = np.array([[26.8500, 75.7600]])

    indices, dists = idx.query_radius_distances(query, radius_m=500.0)
    assert len(indices[0]) == 2
    assert 0 in indices[0]
    assert 1 in indices[0]
    assert 2 not in indices[0]
    assert dists[0][0] < 1.0  # distance to point 0 is ~0m
    assert dists[0][1] < 500.0


def test_nearest_index_exponential_decay_score():
    """Verify exponential_decay_score computes accurate distance-decayed kernel density."""
    targets = np.array([
        [26.8500, 75.7600],
        [26.8500, 75.7600],  # collocated
    ])
    idx = NearestIndex(targets)
    # Query collocated on both points: d=0 for both points => exp(0) + exp(0) = 2.0
    query = np.array([[26.8500, 75.7600]])
    score = idx.exponential_decay_score(query, decay_half_life_m=1000.0)
    assert pytest.approx(score[0], rel=1e-3) == 2.0

    # Validation errors
    with pytest.raises(ValueError, match="decay_half_life_m must be strictly positive"):
        idx.exponential_decay_score(query, decay_half_life_m=-50.0)
