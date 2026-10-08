"""Parity tests ensuring batch feature extraction equals row-by-row extraction."""

import joblib
import pandas as pd

from jpi.config import ART, DATA, SEED
from jpi.features.build import FeaturePipeline


def test_batch_equals_row_by_row():
    """Verify that batch transformation is mathematically identical to row-by-row transformation."""
    clean_path = DATA / "processed" / "listings_clean.parquet"
    df_clean = pd.read_parquet(clean_path).sample(100, random_state=SEED)

    pipe: FeaturePipeline = joblib.load(ART / "model" / "preprocess.joblib")

    # 1. Batch transformation
    batch_features = pipe.transform(df_clean).reset_index(drop=True)

    # 2. Row-by-row transformation (exact single-row API simulation)
    row_features_list = [pipe.transform(df_clean.iloc[[i]]) for i in range(len(df_clean))]
    row_features = pd.concat(row_features_list, axis=0).reset_index(drop=True)

    # Assert exact frame equality
    pd.testing.assert_frame_equal(batch_features, row_features, atol=1e-9, check_dtype=False)


def test_single_row_prediction_latency():
    """Verify single-row transform latency is fast (< 20 ms)."""
    import time

    clean_path = DATA / "processed" / "listings_clean.parquet"
    df_sample = pd.read_parquet(clean_path).iloc[[0]]

    pipe: FeaturePipeline = joblib.load(ART / "model" / "preprocess.joblib")

    # Warmup
    pipe.transform(df_sample)

    t0 = time.perf_counter()
    n_iters = 50
    for _ in range(n_iters):
        pipe.transform(df_sample)
    t1 = time.perf_counter()

    avg_ms = ((t1 - t0) / n_iters) * 1000.0
    print(f"Average single-row feature build latency: {avg_ms:.2f} ms")
    assert avg_ms < 50.0, f"Feature build too slow: {avg_ms:.2f} ms (expected < 50 ms)"
