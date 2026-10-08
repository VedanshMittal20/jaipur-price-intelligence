"""Locality canonicalisation, fuzzy resolution, and coordinate mapping."""

import json
import re
from typing import Dict, Tuple

import pandas as pd
from rapidfuzz import fuzz, process

from jpi.config import CITY_CENTER, DATA, JAIPUR_BBOX


def clean_locality_name(text: str) -> str:
    """Normalize raw locality text for dictionary lookup."""
    if not text or pd.isna(text):
        return "other"
    s = str(text).lower().strip()
    s = re.sub(r"[,\-_/\\]+", " ", s)
    s = re.sub(r"\bjaipur\b", "", s)
    s = re.sub(r"\brajasthan\b", "", s)
    s = re.sub(r"\bindia\b", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else "other"


def load_locality_resources() -> Tuple[Dict[str, str], Dict[str, Dict[str, float]]]:
    """Load canonical locality map and geocode cache."""
    ext_dir = DATA / "external"
    map_csv = ext_dir / "locality_map.csv"
    cache_json = ext_dir / "geocode_cache.json"

    mapping: Dict[str, str] = {}
    if map_csv.exists():
        df_map = pd.read_csv(map_csv)
        for _, r in df_map.iterrows():
            variant = str(r["raw_variant"]).strip().lower()
            canonical = str(r["canonical"]).strip().lower()
            mapping[variant] = canonical

    geocode_cache: Dict[str, Dict[str, float]] = {}
    if cache_json.exists():
        with open(cache_json, "r", encoding="utf-8") as f:
            geocode_cache = json.load(f)

    return mapping, geocode_cache


def resolve_localities_and_coords(df: pd.DataFrame) -> pd.DataFrame:
    """Assign standardized locality_id and coordinate centroids across all rows."""
    mapping, geocode_cache = load_locality_resources()
    canonical_choices = list(geocode_cache.keys())

    resolved_locs = []
    lats = []
    lons = []
    precisions = []

    south, west, north, east = JAIPUR_BBOX
    # Allow 0.15 degree buffer for outer metropolitan fringes
    lat_min, lat_max = south - 0.15, north + 0.15
    lon_min, lon_max = west - 0.15, east + 0.15

    for _, r in df.iterrows():
        raw = clean_locality_name(r.get("locality_raw", ""))

        # 1. Direct dictionary match
        if raw in mapping:
            loc_id = mapping[raw]
        else:
            # Fuzzy match with high threshold (>= 90)
            match = process.extractOne(raw, canonical_choices, scorer=fuzz.token_set_ratio)
            if match and match[1] >= 90:
                loc_id = match[0]
            else:
                loc_id = "other"

        resolved_locs.append(loc_id)

        # 2. Coordinates resolution
        row_lat = r.get("lat")
        row_lon = r.get("lon")
        has_coords = (
            pd.notna(row_lat)
            and pd.notna(row_lon)
            and (lat_min <= float(row_lat) <= lat_max)
            and (lon_min <= float(row_lon) <= lon_max)
        )

        if has_coords and r.get("coord_precision") == "exact":
            lats.append(float(row_lat))
            lons.append(float(row_lon))
            precisions.append("exact")
        else:
            # Assign locality centroid from cache
            if loc_id in geocode_cache:
                c = geocode_cache[loc_id]
                lats.append(float(c["lat"]))
                lons.append(float(c["lon"]))
            else:
                lats.append(CITY_CENTER[0])
                lons.append(CITY_CENTER[1])
            precisions.append("locality_centroid")

    df = df.copy()
    df["locality_id"] = resolved_locs
    df["lat"] = lats
    df["lon"] = lons
    df["coord_precision"] = precisions
    return df
