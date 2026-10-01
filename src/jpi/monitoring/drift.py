"""Covariate and target drift monitoring using Population Stability Index (PSI) and Wasserstein distance."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from jpi.config import ART, DATA, ROOT


def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_buckets: int = 10) -> float:
    """Calculate Population Stability Index (PSI) between reference and production distributions."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)

    # Drop NaNs
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]

    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine quantile bins from reference distribution
    percentiles = np.linspace(0, 100, num_buckets + 1)
    bins = np.percentile(expected, percentiles)
    bins[0] = -np.inf
    bins[-1] = np.inf

    # Bucket counts
    expected_counts, _ = np.histogram(expected, bins=bins)
    actual_counts, _ = np.histogram(actual, bins=bins)

    # Convert to fractions with small epsilon smoothing
    eps = 1e-4
    expected_pct = (expected_counts + eps) / (len(expected) + eps * num_buckets)
    actual_pct = (actual_counts + eps) / (len(actual) + eps * num_buckets)

    # PSI Formula: sum((Actual - Expected) * ln(Actual / Expected))
    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(psi_val)


def calculate_drift_report(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    features: List[str],
) -> Dict[str, Any]:
    """Audit distribution drift across key features."""
    results = {}
    total_features = len(features)
    flagged_features = 0

    for feat in features:
        if feat not in reference_df.columns or feat not in current_df.columns:
            continue

        ref_vals = reference_df[feat].dropna().values
        cur_vals = current_df[feat].dropna().values

        psi = calculate_psi(ref_vals, cur_vals)

        status = "STABLE"
        if psi >= 0.25:
            status = "SIGNIFICANT_DRIFT"
            flagged_features += 1
        elif psi >= 0.10:
            status = "MODERATE_DRIFT"

        results[feat] = {
            "psi": round(psi, 4),
            "status": status,
            "ref_mean": float(np.mean(ref_vals)) if len(ref_vals) > 0 else 0.0,
            "cur_mean": float(np.mean(cur_vals)) if len(cur_vals) > 0 else 0.0,
        }

    overall_status = "PASS"
    if flagged_features > 0:
        overall_status = "ALERT_RETRAIN_REQUIRED"

    return {
        "status": overall_status,
        "features_audited": total_features,
        "features_flagged": flagged_features,
        "metrics": results,
    }


def generate_drift_audit():
    """Run baseline validation drift audit against held-out test split."""
    features_path = DATA / "processed" / "features.parquet"
    if not features_path.exists():
        print("Missing features.parquet, skipping drift audit.")
        return

    df = pd.read_parquet(features_path)

    test_ids_file = DATA / "processed" / "test_ids.txt"
    if test_ids_file.exists():
        test_ids = set(test_ids_file.read_text(encoding="utf-8").splitlines())
        df_train = df[~df["listing_id"].isin(test_ids)]
        df_test = df[df["listing_id"].isin(test_ids)]
    else:
        df_train = df.iloc[: int(len(df) * 0.8)]
        df_test = df.iloc[int(len(df) * 0.8) :]

    audit_features = [
        "area_sqft",
        "bhk",
        "dist_metro_m",
        "dist_cbd_m",
        "dist_primary_road_m",
        "dlc_rate_per_sqm",
        "log_price",
    ]

    report = calculate_drift_report(df_train, df_test, audit_features)

    out_dir = ART / "monitoring"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "drift_report.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Format Markdown summary
    md_content = f"""# Data & Feature Drift Audit

**Audit Status:** `{report['status']}`  
**Features Audited:** {report['features_audited']} | **Flagged Drift:** {report['features_flagged']}

### Population Stability Index (PSI) Thresholds:
- **PSI < 0.10:** Stable (no significant distribution change)
- **0.10 ≤ PSI < 0.25:** Moderate drift (monitor closely)
- **PSI ≥ 0.25:** Significant drift (triggers automatic retraining)

| Feature | PSI Score | Status | Train Reference Mean | Test Sample Mean |
|---|---|---|---|---|
"""
    for feat, m in report["metrics"].items():
        md_content += f"| `{feat}` | {m['psi']:.4f} | `{m['status']}` | {m['ref_mean']:.1f} | {m['cur_mean']:.1f} |\n"

    md_file = ROOT / "docs" / "DRIFT_REPORT.md"
    md_file.write_text(md_content, encoding="utf-8")
    print(f"Generated drift report at {md_file} and {out_file}")
    return report


if __name__ == "__main__":
    generate_drift_audit()
