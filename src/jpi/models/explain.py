"""Exact multiplicative factor explanations via native LightGBM tree contributions."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import lightgbm as lgb
import numpy as np
import pandas as pd

from jpi.config import ART


def explain_prediction(
    contrib_row: np.ndarray,
    feature_names: List[str],
    groups: Dict[str, str],
    labels: Dict[str, str],
    top_k: int = 8,
) -> Dict[str, Any]:
    """Convert native log-space tree contributions into exact multiplicative factors."""
    base = float(contrib_row[-1])  # expected value / intercept
    c = np.asarray(contrib_row[:-1], dtype=float)

    # Group log contributions
    g_contrib: Dict[str, float] = {}
    for name, v in zip(feature_names, c, strict=False):
        grp = groups.get(name, "Other")
        g_contrib[grp] = g_contrib.get(grp, 0.0) + float(v)

    typical_price = float(np.exp(base))
    estimate_price = float(np.exp(base + np.sum(c)))

    # Feature-level breakdown
    feat_effects = []
    for name, v in zip(feature_names, c, strict=False):
        factor = float(np.exp(v))
        pct = float((factor - 1.0) * 100.0)
        feat_effects.append(
            {
                "feature": name,
                "label": labels.get(name, name),
                "factor": factor,
                "effect_pct": pct,
                "abs_log_contrib": abs(float(v)),
            }
        )
    feat_effects.sort(key=lambda d: d["abs_log_contrib"], reverse=True)

    # Group-level breakdown
    group_effects = []
    for grp, v in g_contrib.items():
        factor = float(np.exp(v))
        pct = float((factor - 1.0) * 100.0)
        group_effects.append(
            {
                "group": grp,
                "factor": factor,
                "effect_pct": pct,
            }
        )

    return {
        "typical_price_inr": typical_price,
        "estimate_inr": estimate_price,
        "features": feat_effects[:top_k],
        "groups": group_effects,
    }


def explain_dataframe(
    booster: lgb.Booster,
    X: pd.DataFrame,
    groups_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Generate exact multiplicative explanations for all rows in a DataFrame."""
    if groups_path is None:
        groups_path = ART / "model" / "feature_groups.json"

    with open(groups_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    groups = meta["groups"]
    labels = meta["labels"]

    contribs = booster.predict(X, pred_contrib=True)
    feature_names = list(X.columns)

    explanations = []
    for i in range(len(X)):
        exp = explain_prediction(contribs[i], feature_names, groups, labels)
        explanations.append(exp)

    return explanations
