"""Data cleaning, unit normalisation, deduplication, and outlier filtering."""

import re
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from jpi.config import (
    DATA,
    MAX_AREA_SQFT,
    MAX_PPSF,
    MIN_AREA_SQFT,
    MIN_PPSF,
)


def parse_price_to_inr(val: Any) -> Optional[float]:
    """Convert arbitrary price strings (Lakh, Crore, ₹, comma-separated) to float INR."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else None

    s = str(val).strip().replace(",", "").replace("₹", "").replace("Rs.", "").strip()

    # Match Crore / Cr
    cr_match = re.search(r"([\d\.]+)\s*(?:cr|crore|crores)", s, re.IGNORECASE)
    if cr_match:
        return float(cr_match.group(1)) * 10_000_000.0

    # Match Lakh / Lac / Lacs / L
    lac_match = re.search(r"([\d\.]+)\s*(?:lakh|lacs|lac|l)", s, re.IGNORECASE)
    if lac_match:
        return float(lac_match.group(1)) * 100_000.0

    # Pure number (e.g. "4900000")
    num_match = re.search(r"[-+]?\d*\.?\d+", s)
    if num_match:
        n = float(num_match.group(0))
        # If number is small (< 1000), it's likely entered in Lakhs
        if 1.0 <= n <= 500.0:
            return n * 100_000.0
        return n if n > 0 else None

    return None


def parse_area_to_sqft(val: Any) -> Optional[float]:
    """Convert area expressions (sq ft, sq yd, sq m) to square feet."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else None

    s = str(val).strip().replace(",", "").lower()

    # Square yards (gaj)
    yd_match = re.search(r"([\d\.]+)\s*(?:sq\.?\s*yd|sq\s*yards?|sqyd|yards?|gaj)", s)
    if yd_match:
        return float(yd_match.group(1)) * 9.0

    # Square meters
    m_match = re.search(r"([\d\.]+)\s*(?:sq\.?\s*m|sq\s*meters?|sqm)", s)
    if m_match:
        return float(m_match.group(1)) * 10.7639

    # Square feet default
    num_match = re.search(r"[-+]?\d*\.?\d+", s)
    if num_match:
        n = float(num_match.group(0))
        return n if n > 0 else None

    return None


def deduplicate_listings(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Deduplicate exact and near-duplicate listings."""
    stats = {}
    n_start = len(df)

    # 1. Exact duplicates on key features
    subset_exact = ["source", "price_inr", "area_sqft", "bhk", "locality_raw"]
    df = df.drop_duplicates(subset=subset_exact, keep="first")
    stats["exact_duplicates_dropped"] = n_start - len(df)

    # 2. Near duplicates within same locality with identical price and area
    n_before_near = len(df)
    df["area_rounded"] = (df["area_sqft"] / 10).round() * 10
    df["price_rounded"] = (df["price_inr"] / 50000).round() * 50000
    df = df.drop_duplicates(
        subset=["locality_raw", "bhk", "area_rounded", "price_rounded"], keep="first"
    )
    df = df.drop(columns=["area_rounded", "price_rounded"])
    stats["near_duplicates_dropped"] = n_before_near - len(df)

    return df, stats


def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate price-per-sq-ft and flag outliers using MAD within locality groups."""
    df = df.copy()
    df["ppsf"] = df["price_inr"] / df["area_sqft"]
    df["log_ppsf"] = np.log(df["ppsf"])

    # Global bounds
    is_hard_outlier = (
        (df["price_inr"] <= 0)
        | (df["area_sqft"] < MIN_AREA_SQFT)
        | (df["area_sqft"] > MAX_AREA_SQFT)
        | (df["bhk"] < 1)
        | (df["bhk"] > 10)
    )

    # Locality-grouped robust Z-score (median / MAD)
    def robust_z(s):
        if len(s) < 10:
            return pd.Series(0.0, index=s.index)
        med = s.median()
        mad = np.median(np.abs(s - med))
        if mad < 1e-6:
            return pd.Series(0.0, index=s.index)
        return 0.6745 * (s - med) / mad

    z_scores = df.groupby("locality_id", group_keys=False)["log_ppsf"].apply(robust_z)
    is_statistical_outlier = (
        (z_scores.abs() > 3.5) | (df["ppsf"] < MIN_PPSF) | (df["ppsf"] > MAX_PPSF)
    )

    df["is_outlier"] = is_hard_outlier | is_statistical_outlier
    return df


def clean_and_process_all() -> pd.DataFrame:
    """End-to-end cleaning pipeline from interim to processed parquet."""
    interim_path = DATA / "interim" / "listings_std.parquet"
    processed_dir = DATA / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    if not interim_path.exists():
        from jpi.data.ingest import ingest_all

        df = ingest_all()
    else:
        df = pd.read_parquet(interim_path)

    # 1. Deduplicate
    df, dedup_stats = deduplicate_listings(df)

    # 2. Locality mapping & Geocoding
    from jpi.data.locality import resolve_localities_and_coords

    df = resolve_localities_and_coords(df)

    # 3. Flag Outliers
    df = flag_outliers(df)

    # Filter out hard outliers for modelling dataset
    df_clean = df[~df["is_outlier"]].reset_index(drop=True)

    out_file = processed_dir / "listings_clean.parquet"
    df_clean.to_parquet(out_file, index=False)
    print(f"Cleaned dataset: {len(df_clean)} rows saved to {out_file}.")
    return df_clean


if __name__ == "__main__":
    clean_and_process_all()
