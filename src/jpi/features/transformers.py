"""Custom scikit-learn compatible transformers for leakage-safe feature engineering."""

from typing import Optional, Union

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.neighbors import BallTree


class KNNPriceFeature(BaseEstimator, TransformerMixin):
    """Median and std of log price-per-sq-ft among the k nearest TRAINING listings.

    Strictly leakage-safe: excludes self during training, refit per CV fold.
    Input: DataFrame with ['lat', 'lon', 'area_sqft'].
    Target: y = log(price_inr).
    """

    def __init__(self, k: int = 10):
        self.k = k
        self.tree_: Optional[BallTree] = None
        self.log_ppsf_: Optional[np.ndarray] = None

    def _pts(self, X: pd.DataFrame) -> np.ndarray:
        return np.radians(np.asarray(X[["lat", "lon"]], dtype=float))

    def fit(self, X: pd.DataFrame, y: Optional[Union[np.ndarray, pd.Series]] = None):
        if y is None:
            raise ValueError("Target y (log price) required to fit KNNPriceFeature")
        if len(X) <= self.k + 1:
            raise ValueError(f"Not enough training rows ({len(X)}) for k={self.k}")

        self.tree_ = BallTree(self._pts(X), metric="haversine")
        y_arr = np.asarray(y, dtype=float)
        area_arr = np.asarray(X["area_sqft"], dtype=float)
        self.log_ppsf_ = y_arr - np.log(area_arr)
        return self

    def fit_transform(self, X: pd.DataFrame, y: Optional[Union[np.ndarray, pd.Series]] = None, **kw) -> np.ndarray:
        self.fit(X, y)
        assert self.tree_ is not None
        _, idx = self.tree_.query(self._pts(X), k=self.k + 1)
        n = len(idx)
        is_self = idx == np.arange(n)[:, None]
        drop = np.where(is_self.any(axis=1), is_self.argmax(axis=1), self.k)
        keep = np.ones_like(idx, dtype=bool)
        keep[np.arange(n), drop] = False  # remove self
        return self._summ(idx[keep].reshape(n, self.k))

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        if self.tree_ is None or self.log_ppsf_ is None:
            raise RuntimeError("KNNPriceFeature not fitted")
        _, idx = self.tree_.query(self._pts(X), k=self.k)
        return self._summ(idx)

    def _summ(self, idx: np.ndarray) -> np.ndarray:
        assert self.log_ppsf_ is not None
        v = self.log_ppsf_[idx]
        return np.c_[np.median(v, axis=1), v.std(axis=1)]

    def get_feature_names_out(self, input_features=None) -> np.ndarray:
        return np.array(["knn_log_ppsf_median", "knn_log_ppsf_std"])
