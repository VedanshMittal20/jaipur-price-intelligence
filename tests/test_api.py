"""Integration and endpoint validation tests for the FastAPI production API."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from jpi.config import JAIPUR_BBOX


@pytest.fixture(scope="module")
def client():
    """Shared TestClient running the FastAPI app lifespan."""
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    """GET /health returns 200 and reports healthy state with 35 loaded features."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["features_loaded"] == 35
    assert data["model_version"] == "2.0.0"


def test_model_metadata_endpoint(client):
    """GET /meta/model returns empirical spatial cross-validation and test set metrics."""
    resp = client.get("/meta/model")
    assert resp.status_code == 200
    data = resp.json()
    assert data["features_count"] == 35
    assert 0.15 <= data["test_mape"] <= 0.35
    assert data["test_r2"] >= 0.70
    assert 0.70 <= data["empirical_coverage"] <= 0.90


def test_localities_endpoint(client):
    """GET /localities returns canonical residential clusters with valid coordinates and medians."""
    resp = client.get("/localities")
    assert resp.status_code == 200
    locs = resp.json()
    assert len(locs) >= 30
    min_lat, min_lon, max_lat, max_lon = JAIPUR_BBOX
    for loc in locs:
        assert "locality_id" in loc
        assert "name" in loc
        assert min_lat <= loc["lat"] <= max_lat
        assert min_lon <= loc["lon"] <= max_lon
        assert loc["median_price_inr"] > 500_000
        assert loc["median_ppsf"] > 1_000
        assert loc["listing_count"] >= 3


def test_deals_endpoint(client):
    """GET /deals returns verified market listings priced at least 15% below predicted fair value."""
    resp = client.get("/deals?limit=20")
    assert resp.status_code == 200
    deals = resp.json()
    assert len(deals) > 0
    assert len(deals) <= 20
    for d in deals:
        assert d["discount_pct"] <= -15.0
        assert d["actual_price_inr"] < d["predicted_price_inr"]
        assert d["bhk"] >= 1
        assert d["area_sqft"] >= 100.0


def test_predict_success_with_locality(client):
    """POST /predict generates valuation, calibrated interval, and exact factor breakdown."""
    payload = {
        "area_sqft": 1350.0,
        "bhk": 3,
        "bathrooms": 3,
        "floor": 3,
        "locality": "Mansarovar",
        "property_type": "Apartment",
        "furnishing": "Semi-Furnished",
        "possession_status": "Ready to Move",
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    res = resp.json()

    assert res["estimate_inr"] > 1_000_000
    assert res["interval_low_inr"] < res["estimate_inr"] < res["interval_high_inr"]
    assert res["interval_low_ppsf"] < res["estimate_ppsf"] < res["interval_high_ppsf"]
    assert pytest.approx(res["estimate_ppsf"], rel=1e-3) == res["estimate_inr"] / payload["area_sqft"]
    assert res["coord_precision"] == "locality_centroid"
    assert len(res["factors"]) > 0
    assert len(res["groups"]) > 0


def test_predict_success_with_exact_coords(client):
    """POST /predict resolves exact coordinates and associates nearest micro-market."""
    payload = {
        "area_sqft": 1800.0,
        "bhk": 3,
        "lat": 26.907,
        "lon": 75.743,  # Vaishali Nagar
        "property_type": "Apartment",
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    res = resp.json()
    assert res["coord_precision"] == "exact"
    assert res["lat"] == 26.907
    assert res["lon"] == 75.743


def test_predict_rejects_out_of_bounds_coords(client):
    """POST /predict rejects coordinates outside Jaipur bounding box."""
    # Delhi latitude
    payload = {
        "area_sqft": 1000.0,
        "bhk": 2,
        "lat": 28.6139,
        "lon": 77.2090,
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 422


def test_predict_rejects_invalid_area_or_bhk(client):
    """POST /predict validates structural physical boundaries."""
    resp1 = client.post("/predict", json={"area_sqft": 50.0, "bhk": 2, "locality": "mansarovar"})
    assert resp1.status_code == 422

    resp2 = client.post("/predict", json={"area_sqft": 1200.0, "bhk": 0, "locality": "mansarovar"})
    assert resp2.status_code == 422


def test_predict_rejects_unresolvable_locality_and_coords(client):
    """POST /predict returns 400 when neither valid coords nor recognizable locality provided."""
    payload = {
        "area_sqft": 1200.0,
        "bhk": 2,
        "locality": "RandomNonExistentPlaceXYZ987",
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 400


def test_counterfactual_endpoint(client):
    """POST /counterfactual returns valid scenarios with delta values."""
    payload = {
        "area_sqft": 1400.0,
        "bhk": 3,
        "bathrooms": 2,
        "locality": "Mansarovar",
        "property_type": "Apartment",
        "furnishing": "Semi-Furnished",
        "possession_status": "Ready to Move",
        "floor": 1,
    }
    resp = client.post("/counterfactual", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["baseline_estimate_inr"] > 1_000_000
    assert len(data["scenarios"]) >= 3
    for s in data["scenarios"]:
        assert "scenario_id" in s
        assert "title" in s
        assert "delta_inr" in s
        assert "delta_pct" in s
        assert s["new_estimate_inr"] > 0


def test_locality_insight_endpoint(client):
    """GET /localities/{id}/insight returns grounded narrative and key drivers."""
    resp = client.get("/localities/mansarovar/insight")
    assert resp.status_code == 200
    data = resp.json()

    assert data["name"] == "Mansarovar"
    assert "tier" in data
    assert "narrative" in data
    assert len(data["key_drivers"]) >= 2
    assert data["listing_count"] > 10

    # Non-existent locality returns 404
    resp_404 = client.get("/localities/non_existent_micro_market_xyz/insight")
    assert resp_404.status_code == 404


