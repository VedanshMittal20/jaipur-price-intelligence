"""Shared nearest-neighbor and spatial radius query classes using Haversine BallTree."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.neighbors import BallTree

EARTH_R_M = 6_371_000.0


class NearestIndex:
    """Haversine BallTree over [lat, lon] degrees; identical code path in training and serving."""

    def __init__(self, latlon_deg: Union[np.ndarray, list]):
        pts = np.asarray(latlon_deg, dtype=float)
        if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) == 0:
            raise ValueError("need a non-empty (n, 2) array of [lat, lon] degrees")
        self._pts = pts
        self._tree = BallTree(np.radians(pts), metric="haversine")

    def nearest_m(self, query_deg: Union[np.ndarray, list]) -> np.ndarray:
        """Calculate distance in meters to the nearest point."""
        q = np.asarray(query_deg, dtype=float)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        d, _ = self._tree.query(np.radians(q), k=1)
        return d[:, 0] * EARTH_R_M

    def k_nearest_m(self, query_deg: Union[np.ndarray, list], k: int = 1) -> np.ndarray:
        """Calculate distances in meters to the k nearest points."""
        if k < 1:
            raise ValueError("k must be at least 1")
        if k > len(self._pts):
            raise ValueError(f"k={k} exceeds indexed point count ({len(self._pts)})")
        q = np.asarray(query_deg, dtype=float)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        d, _ = self._tree.query(np.radians(q), k=k)
        return d * EARTH_R_M

    def nearest_with_index(
        self, query_deg: Union[np.ndarray, list], k: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate distances in meters and indices to the k nearest points."""
        if k < 1:
            raise ValueError("k must be at least 1")
        if k > len(self._pts):
            raise ValueError(f"k={k} exceeds indexed point count ({len(self._pts)})")
        q = np.asarray(query_deg, dtype=float)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        d, idx = self._tree.query(np.radians(q), k=k)
        return d * EARTH_R_M, idx

    def count_within(self, query_deg: Union[np.ndarray, list], radius_m: float) -> np.ndarray:
        """Count points within radius_m meters."""
        q = np.asarray(query_deg, dtype=float)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        return self._tree.query_radius(
            np.radians(q),
            r=radius_m / EARTH_R_M,
            count_only=True,
        )

    def query_radius_distances(
        self, query_deg: Union[np.ndarray, list], radius_m: float
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Return indices and distances in meters for all indexed points within radius_m."""
        if radius_m <= 0:
            raise ValueError("radius_m must be strictly positive")
        q = np.asarray(query_deg, dtype=float)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        indices, dists_rad = self._tree.query_radius(
            np.radians(q),
            r=radius_m / EARTH_R_M,
            return_distance=True,
            sort_results=True,
        )
        dists_m = [d * EARTH_R_M for d in dists_rad]
        return indices, dists_m

    def exponential_decay_score(
        self,
        query_deg: Union[np.ndarray, list],
        decay_half_life_m: float = 1000.0,
        max_radius_m: Optional[float] = None,
    ) -> np.ndarray:
        """Compute distance-decayed spatial accessibility score using exponential kernel."""
        if decay_half_life_m <= 0:
            raise ValueError("decay_half_life_m must be strictly positive")
        cutoff = max_radius_m if max_radius_m is not None else 4.0 * decay_half_life_m
        if cutoff <= 0:
            raise ValueError("max_radius_m must be strictly positive")

        q = np.asarray(query_deg, dtype=float)
        if q.ndim == 1:
            q = q.reshape(1, -1)

        _, dists_rad = self._tree.query_radius(
            np.radians(q),
            r=cutoff / EARTH_R_M,
            return_distance=True,
        )
        lambda_factor = np.log(2.0) / decay_half_life_m
        scores = np.zeros(len(q), dtype=float)
        for i, d_arr in enumerate(dists_rad):
            if len(d_arr) > 0:
                d_m = d_arr * EARTH_R_M
                scores[i] = np.sum(np.exp(-lambda_factor * d_m))
        return scores


class GeoLayers:
    """Dictionary container of NearestIndex layers loaded from geo_layers.npz."""

    def __init__(self, path: Union[str, Path]):
        z = np.load(path)
        self.idx: Dict[str, NearestIndex] = {k: NearestIndex(z[k]) for k in z.files}

    def __getitem__(self, k: str) -> NearestIndex:
        return self.idx[k]

    def keys(self):
        return self.idx.keys()
