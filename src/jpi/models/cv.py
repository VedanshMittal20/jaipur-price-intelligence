"""Spatial block partitioning and cross-validation fold generation."""

from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from jpi.config import DATA, SEED, SPATIAL_BLOCK_DEG


def compute_spatial_blocks(lat: np.ndarray, lon: np.ndarray, size: float = SPATIAL_BLOCK_DEG) -> np.ndarray:
    """Generate spatial block identifiers based on grid resolution (~2.2 km)."""
    lat_arr = np.asarray(lat, dtype=float)
    lon_arr = np.asarray(lon, dtype=float)
    b_lat = np.floor(lat_arr / size).astype(int).astype(str)
    b_lon = np.floor(lon_arr / size).astype(int).astype(str)
    return np.char.add(np.char.add(b_lat, "_"), b_lon)


def create_spatial_splits(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[Tuple[np.ndarray, np.ndarray]]]:
    """Partition dataset into untouched test set and 5-fold grouped CV training folds."""
    df = df.copy()
    blocks = compute_spatial_blocks(df["lat"].values, df["lon"].values)
    df["spatial_block"] = blocks

    # 1. Carve out final test set (20% of spatial blocks)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SEED)
    train_idx, test_idx = next(gss.split(df, groups=df["spatial_block"]))

    df_train = df.iloc[train_idx].copy().reset_index(drop=True)
    df_test = df.iloc[test_idx].copy().reset_index(drop=True)

    # Save test IDs - frozen until final evaluation M8
    test_ids_file = DATA / "processed" / "test_ids.txt"
    test_ids_file.parent.mkdir(parents=True, exist_ok=True)
    with open(test_ids_file, "w", encoding="utf-8") as f:
        f.write("\n".join(df_test["listing_id"].astype(str).tolist()))

    # 2. Build 5 reproducible spatial CV folds on df_train
    gkf = GroupKFold(n_splits=5)
    train_folds: List[Tuple[np.ndarray, np.ndarray]] = list(
        gkf.split(df_train, groups=df_train["spatial_block"])
    )

    print(f"Spatial splitting complete:")
    print(f"  - Total blocks: {len(np.unique(blocks))}")
    print(f"  - Training set: {len(df_train)} rows across {len(np.unique(df_train['spatial_block']))} blocks")
    print(f"  - Held-out test set: {len(df_test)} rows across {len(np.unique(df_test['spatial_block']))} blocks")
    print(f"  - Test IDs frozen to: {test_ids_file}")

    return df_train, df_test, train_folds


if __name__ == "__main__":
    features_df = pd.read_parquet(DATA / "processed" / "features.parquet")
    create_spatial_splits(features_df)
