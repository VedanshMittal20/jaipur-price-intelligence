"""Evaluation metrics harness and baseline models for real estate price intelligence."""

from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score


def price_metrics(y_log_true: np.ndarray, y_log_pred: np.ndarray) -> Dict[str, float]:
    """Calculate price metrics on original rupee scale and R2 on log scale."""
    y = np.exp(np.asarray(y_log_true, dtype=float))
    p = np.exp(np.asarray(y_log_pred, dtype=float))

    ape = np.abs(p - y) / y
    mape = float(np.mean(ape))
    med_ape = float(np.median(ape))
    mae = float(np.mean(np.abs(p - y)))
    rmse = float(np.sqrt(np.mean((p - y) ** 2)))
    r2_log = float(r2_score(y_log_true, y_log_pred))

    return {
        "mape": mape,
        "median_ape": med_ape,
        "mae_inr": mae,
        "rmse_inr": rmse,
        "r2_log": r2_log,
    }


def oof_predict(
    make_model: Callable[[], object],
    X: pd.DataFrame,
    y_log: np.ndarray,
    folds: List[Tuple[np.ndarray, np.ndarray]],
) -> np.ndarray:
    """Compute out-of-fold predictions across pre-partitioned folds."""
    oof = np.full(len(y_log), np.nan)
    for tr, va in folds:
        m = make_model()
        m.fit(X.iloc[tr], y_log[tr])
        oof[va] = m.predict(X.iloc[va])
    return oof


def evaluate_baseline_a0(
    df: pd.DataFrame, folds: List[Tuple[np.ndarray, np.ndarray]]
) -> Tuple[np.ndarray, Dict[str, float]]:
    """Baseline A0: Locality median price-per-sq-ft * area (fallback to global median)."""
    y_log = df["log_price"].values
    areas = df["area_sqft"].values
    locs = df["locality_id"].values
    oof_pred_log = np.full(len(df), np.nan)

    for tr, va in folds:
        tr_df = pd.DataFrame({"loc": locs[tr], "ppsf": np.exp(y_log[tr]) / areas[tr]})
        global_med_ppsf = tr_df["ppsf"].median()
        loc_med_map = tr_df.groupby("loc")["ppsf"].median().to_dict()

        for idx in va:
            l = locs[idx]
            ppsf_est = loc_med_map.get(l, global_med_ppsf)
            oof_pred_log[idx] = np.log(ppsf_est * areas[idx])

    metrics = price_metrics(y_log, oof_pred_log)
    return oof_pred_log, metrics
