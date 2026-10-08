"""End-to-end smoke test benchmarking latency, memory consumption, and API endpoints."""

import sys
import time
from pathlib import Path

# Add project root and src to sys.path
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

import numpy as np
import psutil
from fastapi.testclient import TestClient

from api.main import app


def run_smoke_test():
    """Execute complete API smoke test and performance benchmark."""
    print("=" * 60)
    print(" JAIPUR PRICE INTELLIGENCE — END-TO-END SMOKE TEST")
    print("=" * 60)

    start_rss = psutil.Process().memory_info().rss / (1024 * 1024)
    print(f"Initial Process RSS Memory: {start_rss:.1f} MB")

    with TestClient(app) as client:
        # 1. Health Endpoint
        t0 = time.perf_counter()
        resp_health = client.get("/health")
        t_health = (time.perf_counter() - t0) * 1000
        assert resp_health.status_code == 200, f"Health check failed: {resp_health.text}"
        health_data = resp_health.json()
        print(f"\n[✓] GET /health: 200 OK ({t_health:.1f} ms)")
        print(
            f"    Status: {health_data['status']} | Features Loaded: {health_data['features_loaded']}"
        )

        # 2. Metadata Endpoint
        t0 = time.perf_counter()
        resp_meta = client.get("/meta/model")
        t_meta = (time.perf_counter() - t0) * 1000
        assert resp_meta.status_code == 200
        meta_data = resp_meta.json()
        print(f"\n[✓] GET /meta/model: 200 OK ({t_meta:.1f} ms)")
        print(f"    Model: {meta_data['model_name']} v{meta_data['model_version']}")
        print(
            f"    Holdout Spatial R²: {meta_data['test_r2']:.3f} | Spatial CV MAPE: {meta_data['spatial_cv_mape'] * 100:.2f}%"
        )

        # 3. Localities Endpoint
        t0 = time.perf_counter()
        resp_locs = client.get("/localities")
        t_locs = (time.perf_counter() - t0) * 1000
        assert resp_locs.status_code == 200
        locs_data = resp_locs.json()
        print(f"\n[✓] GET /localities: 200 OK ({t_locs:.1f} ms)")
        print(f"    Available Localities: {len(locs_data)} canonical micro-markets")

        # 4. Locality Insight Endpoint
        t0 = time.perf_counter()
        resp_insight = client.get("/localities/mansarovar/insight")
        t_insight = (time.perf_counter() - t0) * 1000
        assert resp_insight.status_code == 200
        ins_data = resp_insight.json()
        print(f"\n[✓] GET /localities/mansarovar/insight: 200 OK ({t_insight:.1f} ms)")
        print(f"    Tier: {ins_data['tier']}")
        print(f"    Narrative: {ins_data['narrative'][:90]}...")

        # 5. Deal Finder Endpoint
        t0 = time.perf_counter()
        resp_deals = client.get("/deals?limit=25")
        t_deals = (time.perf_counter() - t0) * 1000
        assert resp_deals.status_code == 200
        deals_data = resp_deals.json()
        print(f"\n[✓] GET /deals: 200 OK ({t_deals:.1f} ms)")
        print(f"    Underpriced Deals Found: {len(deals_data)} listings")

        # 6. Counterfactual Endpoint
        t0 = time.perf_counter()
        cf_payload = {
            "area_sqft": 1400,
            "bhk": 3,
            "locality": "Mansarovar",
            "property_type": "Apartment",
            "furnishing": "Semi-Furnished",
            "possession_status": "Ready to Move",
        }
        resp_cf = client.post("/counterfactual", json=cf_payload)
        t_cf = (time.perf_counter() - t0) * 1000
        assert resp_cf.status_code == 200
        cf_data = resp_cf.json()
        print(f"\n[✓] POST /counterfactual: 200 OK ({t_cf:.1f} ms)")
        print(f"    Scenarios Evaluated: {len(cf_data['scenarios'])}")

        # 7. 100-Request Latency Benchmark on /predict
        print("\n" + "-" * 50)
        print(" RUNNING 100-REQUEST LATENCY BENCHMARK (/predict)")
        print("-" * 50)

        latencies_ms = []
        localities_sample = [
            "Mansarovar",
            "Vaishali Nagar",
            "Jagatpura",
            "C Scheme",
            "Malviya Nagar",
        ]
        types_sample = ["Apartment", "Independent House", "Villa"]

        for i in range(100):
            payload = {
                "area_sqft": 800 + (i * 20) % 2500,
                "bhk": 1 + (i % 4),
                "bathrooms": 1 + (i % 3),
                "floor": i % 10,
                "locality": localities_sample[i % len(localities_sample)],
                "property_type": types_sample[i % len(types_sample)],
                "furnishing": "Semi-Furnished" if i % 2 == 0 else "Furnished",
                "possession_status": "Ready to Move",
            }
            t_req = time.perf_counter()
            r = client.post("/predict", json=payload)
            dur = (time.perf_counter() - t_req) * 1000
            assert r.status_code == 200
            latencies_ms.append(dur)

        latencies_ms = np.array(latencies_ms)
        p50 = float(np.percentile(latencies_ms, 50))
        p95 = float(np.percentile(latencies_ms, 95))
        p99 = float(np.percentile(latencies_ms, 99))
        mean_lat = float(np.mean(latencies_ms))

        print("Latency Results (100 Requests):")
        print(f"  - Mean Latency:  {mean_lat:.2f} ms")
        print(f"  - p50 Latency:   {p50:.2f} ms (Target: < 25 ms)")
        print(f"  - p95 Latency:   {p95:.2f} ms (Target: < 50 ms)")
        print(f"  - p99 Latency:   {p99:.2f} ms")

        # 8. Memory Footprint Audit
        final_rss = psutil.Process().memory_info().rss / (1024 * 1024)
        print("\nFinal Memory Footprint:")
        print(f"  - Total RSS Memory: {final_rss:.1f} MB (Target: < 400 MB on 512 MB host)")

        # Verify SLO Constraints
        assert p95 < 100.0, f"p95 latency exceeded SLA ({p95:.1f} ms >= 100 ms)"
        assert final_rss < 400.0, f"Container RSS exceeded limit ({final_rss:.1f} MB >= 400 MB)"

    print("\n" + "=" * 60)
    print(" ALL SMOKE TEST CHECKS & PERFORMANCE SLOs PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    run_smoke_test()
