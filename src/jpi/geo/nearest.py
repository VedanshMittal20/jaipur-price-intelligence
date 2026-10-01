"""Shared nearest-neighbor and spatial radius query classes using Haversine BallTree."""

from pathlib import Path
from typing import Dict, Union

import numpy as np
from sklearn.neighbors import BallTree

EARTH_R_M = 6_371_000.0


class NearestIndex:
    """Haversine BallTree over [lat, lon] degrees; identical code path in training and serving."""

    def __init__(self, latlon_deg: Union[np.ndarray, list]):
        pts = np.asarray(latlon_deg, dtype=float)
        if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) == 0:
            raise ValueError("need a non-empty (n, 2) array of [lat, lon] degrees")
        self._tree = BallTree(np.radians(pts), metric="haversine")

    def nearest_m(self, query_deg: Union[np.ndarray, list]) -> np.ndarray:
        """Calculate distance in meters to the nearest point."""
        q = np.asarray(query_deg, dtype=float)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        d, _ = self._tree.query(np.radians(q), k=1)
        return d[:, 0] * EARTH_R_M

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


class GeoLayers:
    """Dictionary container of NearestIndex layers loaded from geo_layers.npz."""

    def __init__(self, path: Union[str, Path]):
        z = np.load(path)
        self.idx: Dict[str, NearestIndex] = {k: NearestIndex(z[k]) for k in z.files}

    def __getitem__(self, k: str) -> NearestIndex:
        return self.idx[k]

    def keys(self):
        return self.idx.keys()
