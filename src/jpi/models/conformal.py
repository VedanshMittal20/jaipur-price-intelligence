"""Mondrian conformal prediction calibration for price uncertainty quantification."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from jpi.config import ART, INTERVAL_ALPHA


def compute_conformal_halfwidth(y_log: np.ndarray, pred_log: np.ndarray, alpha: float = INTERVAL_ALPHA) -> float:
    """Calculate finite-sample calibrated conformal halfwidth on log residuals."""
    residuals = np.abs(np.asarray(y_log, dtype=float) - np.asarray(pred_log, dtype=float))
    n = len(residuals)
    if n == 0:
        return 0.25
    q = min(1.0, np.ceil((n + 1) * (1.0 - alpha)) / n)
    return float(np.quantile(residuals, q, method="higher"))


class MondrianConformalCalibrator:
    """Mondrian conformal calibrator partitioned by predicted price terciles."""

    def __init__(self, alpha: float = INTERVAL_ALPHA):
        self.alpha = alpha
        self.global_halfwidth: float = 0.25
        self.tercile_edges: List[float] = []
        self.tercile_halfwidths: List[float] = []

    def fit(self, y_log: np.ndarray, oof_pred_log: np.ndarray):
        """Fit calibration bounds on out-of-fold residuals."""
        self.global_halfwidth = compute_conformal_halfwidth(y_log, oof_pred_log, self.alpha)

        # Partition into 3 terciles based on predicted price
        q33 = float(np.percentile(oof_pred_log, 33.33))
        q66 = float(np.percentile(oof_pred_log, 66.66))
        self.tercile_edges = [q33, q66]

        t1_mask = oof_pred_log <= q33
        t2_mask = (oof_pred_log > q33) & (oof_pred_log <= q66)
        t3_mask = oof_pred_log > q66

        hw1 = compute_conformal_halfwidth(y_log[t1_mask], oof_pred_log[t1_mask], self.alpha)
        hw2 = compute_conformal_halfwidth(y_log[t2_mask], oof_pred_log[t2_mask], self.alpha)
        hw3 = compute_conformal_halfwidth(y_log[t3_mask], oof_pred_log[t3_mask], self.alpha)

        self.tercile_halfwidths = [hw1, hw2, hw3]

    def predict_interval(self, pred_log: float) -> Tuple[float, float, float]:
        """Return (low_inr, point_inr, high_inr) for a single log prediction."""
        if not self.tercile_edges:
            hw = self.global_halfwidth
        elif pred_log <= self.tercile_edges[0]:
            hw = self.tercile_halfwidths[0]
        elif pred_log <= self.tercile_edges[1]:
            hw = self.tercile_halfwidths[1]
        else:
            hw = self.tercile_halfwidths[2]

        point_inr = float(np.exp(pred_log))
        low_inr = float(np.exp(pred_log - hw))
        high_inr = float(np.exp(pred_log + hw))
        return low_inr, point_inr, high_inr

    def evaluate_coverage(self, y_log_test: np.ndarray, pred_log_test: np.ndarray) -> Dict[str, float]:
        """Evaluate empirical coverage on untouched test set."""
        y_test = np.exp(np.asarray(y_log_test, dtype=float))
        p_test = np.asarray(pred_log_test, dtype=float)

        lows, points, highs = [], [], []
        for p in p_test:
            lo, pt, hi = self.predict_interval(p)
            lows.append(lo)
            points.append(pt)
            highs.append(hi)

        lows = np.array(lows)
        highs = np.array(highs)

        covered = (y_test >= lows) & (y_test <= highs)
        overall_coverage = float(np.mean(covered))

        # Coverage by tercile
        q33, q66 = self.tercile_edges if self.tercile_edges else (0, 0)
        t1 = p_test <= q33
        t2 = (p_test > q33) & (p_test <= q66)
        t3 = p_test > q66

        return {
            "nominal_coverage": 1.0 - self.alpha,
            "overall_empirical_coverage": overall_coverage,
            "low_tier_coverage": float(np.mean(covered[t1])) if np.sum(t1) > 0 else overall_coverage,
            "mid_tier_coverage": float(np.mean(covered[t2])) if np.sum(t2) > 0 else overall_coverage,
            "high_tier_coverage": float(np.mean(covered[t3])) if np.sum(t3) > 0 else overall_coverage,
        }

    def save(self, path: Optional[Path] = None):
        """Serialize conformal calibration parameters."""
        if path is None:
            path = ART / "model" / "conformal.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "alpha": self.alpha,
            "global_halfwidth": self.global_halfwidth,
            "tercile_edges": self.tercile_edges,
            "tercile_halfwidths": self.tercile_halfwidths,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Optional[Path] = None):
        """Load calibrator from JSON."""
        if path is None:
            path = ART / "model" / "conformal.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cal = cls(alpha=data["alpha"])
        cal.global_halfwidth = data["global_halfwidth"]
        cal.tercile_edges = data["tercile_edges"]
        cal.tercile_halfwidths = data["tercile_halfwidths"]
        return cal
