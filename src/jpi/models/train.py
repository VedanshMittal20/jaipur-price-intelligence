"""Model ladder, spatial cross-validation, ablation study, and production export."""

import json
from pathlib import Path
from typing import Dict, List, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

from jpi.config import ART, DATA, SEED
from jpi.models.conformal import MondrianConformalCalibrator
from jpi.models.cv import create_spatial_splits
from jpi.models.evaluate import evaluate_baseline_a0, oof_predict, price_metrics


def train_and_evaluate_all():
    """Execute complete modeling phase: splits, ladder, ablation, calibration, and test evaluation."""
    features_path = DATA / "processed" / "features.parquet"
    df_all = pd.read_parquet(features_path)

    # 1. Spatial Splits (M1)
    df_train, df_test, folds = create_spatial_splits(df_all)

    # 1.5 Fix Target Leakage: Recompute spatio_temporal_te out-of-fold for CV
    from sklearn.preprocessing import TargetEncoder

    cv_te = np.zeros(len(df_train))
    y_train_log = df_train["log_price"].values
    st_train = df_train[["spatio_temporal"]]
    for tr, va in folds:
        te = TargetEncoder(target_type="continuous")
        te.fit(st_train.iloc[tr], y_train_log[tr])
        cv_te[va] = te.transform(st_train.iloc[va]).flatten()
    df_train["spatio_temporal_te"] = cv_te

    te_full = TargetEncoder(target_type="continuous")
    te_full.fit(st_train, y_train_log)
    df_test["spatio_temporal_te"] = te_full.transform(df_test[["spatio_temporal"]]).flatten()

    # Separate target and features
    drop_cols = [
        "price_inr",
        "log_price",
        "listing_id",
        "lat",
        "lon",
        "spatial_block",
        "spatio_temporal",
    ]
    feature_cols = [c for c in df_train.columns if c not in drop_cols]

    X_train = df_train[feature_cols]

    X_test = df_test[feature_cols]
    y_test_log = df_test["log_price"].values

    results_data: Dict[str, object] = {}

    # 2. Baseline A0 (M2)
    print("\n--- Evaluating Baseline A0 ---")
    _, a0_metrics = evaluate_baseline_a0(df_train, folds)
    print(
        f"Baseline A0 (Locality Median): MAPE = {a0_metrics['mape'] * 100:.2f}%, R2 = {a0_metrics['r2_log']:.3f}"
    )
    results_data["a0"] = a0_metrics

    # 3. Model Ladder (M3)
    print("\n--- Model Ladder Comparison (Grouped Spatial-CV) ---")
    models = {
        "Ridge": lambda: Ridge(alpha=10.0),
        "RandomForest": lambda: RandomForestRegressor(
            n_estimators=100, max_depth=12, random_state=SEED, n_jobs=-1
        ),
        "LightGBM": lambda: lgb.LGBMRegressor(
            n_estimators=150,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=SEED,
            n_jobs=-1,
            verbosity=-1,
        ),
    }

    ladder_results = {}
    for name, make_fn in models.items():
        oof = oof_predict(make_fn, X_train, y_train_log, folds)
        m = price_metrics(y_train_log, oof)
        ladder_results[name] = m
        print(
            f"  {name:15s}: MAPE = {m['mape'] * 100:.2f}%, MedAPE = {m['median_ape'] * 100:.2f}%, R2 = {m['r2_log']:.3f}"
        )

    results_data["ladder"] = ladder_results

    # Random-CV Comparison on LightGBM to quantify spatial leakage gap
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    random_folds = list(kf.split(df_train))
    oof_random = oof_predict(models["LightGBM"], X_train, y_train_log, random_folds)
    m_random = price_metrics(y_train_log, oof_random)
    m_spatial = ladder_results["LightGBM"]
    leakage_gap = m_spatial["mape"] - m_random["mape"]
    print(
        f"\nSpatial-CV MAPE: {m_spatial['mape'] * 100:.2f}% vs Random-CV MAPE: {m_random['mape'] * 100:.2f}% (Leakage Gap: +{leakage_gap * 100:.2f}%)"
    )
    results_data["random_cv"] = m_random
    results_data["leakage_gap_pct"] = float(leakage_gap * 100.0)

    # 4. Feature Ablation Study (M5)
    print("\n--- Feature Ablation Study ---")
    prop_cols = [
        "area_sqft",
        "bhk",
        "bathrooms",
        "bath_per_bhk",
        "floor",
        "rera_flag",
        "property_type",
        "furnishing",
        "possession_status",
        "posted_by",
    ]
    geo_dist_cols = [
        "dist_metro_m",
        "dist_rail_m",
        "dist_airport_m",
        "dist_primary_road_m",
        "dist_cbd_m",
    ]
    geo_amenity_cols = [
        "dist_hospital_m",
        "dist_school_m",
        "dist_mall_m",
        "dist_park_m",
        "n_school_1000m",
        "n_hospital_1000m",
        "n_restaurant_1000m",
        "n_shop_1000m",
    ]
    dlc_cols = ["dlc_rate_per_sqm", "dlc_missing"]

    ablation_sets = {
        "A1_Property_Only": prop_cols,
        "A2_Plus_Locality": prop_cols + ["locality_id", "coord_precision", "spatio_temporal_te"],
        "A3_Plus_Geo": prop_cols
        + ["locality_id", "coord_precision", "spatio_temporal_te"]
        + geo_dist_cols
        + geo_amenity_cols,
        "A4_Plus_DLC": prop_cols
        + ["locality_id", "coord_precision", "spatio_temporal_te"]
        + geo_dist_cols
        + geo_amenity_cols
        + dlc_cols,
    }

    ablation_results = {}
    for vname, vcols in ablation_sets.items():
        sub_X = X_train[vcols]
        oof = oof_predict(models["LightGBM"], sub_X, y_train_log, folds)
        m = price_metrics(y_train_log, oof)
        ablation_results[vname] = m
        print(
            f"  {vname:20s}: MAPE = {m['mape'] * 100:.2f}%, MedAPE = {m['median_ape'] * 100:.2f}%, R2 = {m['r2_log']:.3f}"
        )

    results_data["ablation"] = ablation_results
    geo_lift = (
        ablation_results["A2_Plus_Locality"]["mape"] - ablation_results["A3_Plus_Geo"]["mape"]
    )
    print(
        f"Geospatial Feature Lift (A2 -> A3 error reduction): {geo_lift * 100:.2f} percentage points!"
    )
    results_data["geo_lift_pct"] = float(geo_lift * 100.0)

    # 5. Conformal Calibration on OOF Residuals (M6)
    print("\n--- Mondrian Conformal Calibration ---")
    oof_best = oof_predict(models["LightGBM"], X_train, y_train_log, folds)
    calibrator = MondrianConformalCalibrator()
    calibrator.fit(y_train_log, oof_best)
    calibrator.save(ART / "model" / "conformal.json")
    print(
        f"Fitted Conformal Halfwidths: Global={calibrator.global_halfwidth:.3f}, Terciles={calibrator.tercile_halfwidths}"
    )

    # 6. Fit Production Model & Benchmark
    print("\n--- Fitting Production Booster & Exporting ---")
    train_data = lgb.Dataset(X_train, label=y_train_log)
    params = {
        "objective": "regression",
        "metric": "l1",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": SEED,
        "verbose": -1,
    }
    booster = lgb.train(params, train_data, num_boost_round=150)
    model_file = ART / "model" / "model.txt"
    booster.save_model(str(model_file))
    print(f"Saved production booster to {model_file}")

    # 7. Final Evaluation on Untouched Test Set ONCE (M8)
    print("\n--- Final Single Evaluation on Untouched Test Set (M8) ---")
    test_pred_log = booster.predict(X_test)
    test_metrics = price_metrics(y_test_log, test_pred_log)
    print(f"Test MAPE:      {test_metrics['mape'] * 100:.2f}% (Target <= 20%)")
    print(f"Test MedianAPE: {test_metrics['median_ape'] * 100:.2f}%")
    print(f"Test R2 (log):  {test_metrics['r2_log']:.3f} (Target >= 0.75)")
    print(f"Test MAE (INR): ₹{test_metrics['mae_inr']:,.0f}")
    print(f"Test RMSE(INR): ₹{test_metrics['rmse_inr']:,.0f}")

    # Coverage on test set
    coverage_results = calibrator.evaluate_coverage(y_test_log, test_pred_log)
    print(f"Nominal Coverage:   {coverage_results['nominal_coverage'] * 100:.1f}%")
    print(
        f"Empirical Coverage: {coverage_results['overall_empirical_coverage'] * 100:.1f}% (Target 75-85%)"
    )
    print(f"  - Low Tier:  {coverage_results['low_tier_coverage'] * 100:.1f}%")
    print(f"  - Mid Tier:  {coverage_results['mid_tier_coverage'] * 100:.1f}%")
    print(f"  - High Tier: {coverage_results['high_tier_coverage'] * 100:.1f}%")

    results_data["test_metrics"] = test_metrics
    results_data["coverage"] = coverage_results

    # Save metrics snapshot
    metrics_json = ART / "model" / "metrics.json"
    with open(metrics_json, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    return results_data


if __name__ == "__main__":
    train_and_evaluate_all()
