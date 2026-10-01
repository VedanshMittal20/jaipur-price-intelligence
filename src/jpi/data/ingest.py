"""Data ingestion pipeline from raw sources to canonical schema."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from jpi.config import DATA, SEED


def make_listing_id(source: str, index: int) -> str:
    """Generate a stable 16-character hex hash identifier."""
    raw = f"{source}:{index}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def parse_numeric(val: Any) -> Optional[float]:
    """Extract numeric value safely."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    match = re.search(r"[-+]?\d*\.?\d+", s)
    return float(match.group(0)) if match else None


def load_karanveer_raw(raw_path: Path) -> pd.DataFrame:
    """Ingest and map Karan Veer Jaipur flats dataset to canonical columns."""
    df = pd.read_csv(raw_path)
    rows: List[Dict[str, Any]] = []

    for idx, r in df.iterrows():
        # Price and Area
        price = parse_numeric(r.get("total_price"))
        area = parse_numeric(r.get("area(sq-ft)"))
        bhk_val = parse_numeric(r.get("bhk"))
        bath_val = parse_numeric(r.get("bath"))

        if price is None or price <= 0 or area is None or area <= 0:
            continue

        bhk = int(bhk_val) if bhk_val and bhk_val > 0 else 2
        bathrooms = int(bath_val) if bath_val and bath_val > 0 else None

        # Locality raw text
        loc = str(r.get("location", "")).strip() or str(r.get("location_area", "")).strip()
        if not loc or loc.lower() in ("unknown", "other"):
            loc = str(r.get("location_area", "")).strip() or "other"

        # Floor
        floor_val = parse_numeric(r.get("floor"))
        floor = int(floor_val) if floor_val is not None and floor_val >= 0 else None

        # Furnishing
        furn_raw = str(r.get("furnished_status", "")).lower()
        if "semi" in furn_raw:
            furnishing = "semi_furnished"
        elif "unfurnished" in furn_raw:
            furnishing = "unfurnished"
        elif "furnished" in furn_raw:
            furnishing = "furnished"
        else:
            furnishing = None

        # Possession
        pos_raw = str(r.get("property_status", "")).lower()
        possession = "ready_to_move" if "ready" in pos_raw else "under_construction"

        # Area type
        area_type = str(r.get("area_type", "Built-up Area")).strip()

        rows.append(
            {
                "listing_id": make_listing_id("karanveer_jaipur", idx),
                "source": "karanveer_jaipur",
                "price_inr": float(price),
                "area_sqft": float(area),
                "area_type": area_type,
                "bhk": bhk,
                "bathrooms": bathrooms,
                "property_type": "apartment",
                "locality_raw": loc,
                "locality_id": None,  # assigned in Phase 3
                "lat": None,
                "lon": None,
                "coord_precision": "locality_centroid",
                "age_years": None,
                "floor": floor,
                "total_floors": None,
                "furnishing": furnishing,
                "possession_status": possession,
                "posted_by": "dealer",  # SquareYards aggregated listings
                "rera_flag": None,
                "listing_date": None,
            }
        )

    return pd.DataFrame(rows)


def load_anmolkumar_raw(raw_path: Path) -> pd.DataFrame:
    """Ingest, filter to Jaipur, and map Anmol Kumar dataset."""
    df = pd.read_csv(raw_path)
    rows: List[Dict[str, Any]] = []

    for idx, r in df.iterrows():
        addr = str(r.get("ADDRESS", ""))
        if not re.search(r"jaipur", addr, re.IGNORECASE):
            continue

        price_lacs = parse_numeric(r.get("TARGET(PRICE_IN_LACS)"))
        area = parse_numeric(r.get("SQUARE_FT"))
        bhk_val = parse_numeric(r.get("BHK_NO."))

        if price_lacs is None or price_lacs <= 0 or area is None or area <= 0:
            continue

        price_inr = float(price_lacs * 100_000.0)
        bhk = int(bhk_val) if bhk_val and bhk_val > 0 else 1

        # Correct for known swapped coordinate bug in Anmol Kumar dataset
        # Original LONGITUDE has ~26.9 (latitude), LATITUDE has ~75.8 (longitude)
        raw_lat = parse_numeric(r.get("LONGITUDE"))
        raw_lon = parse_numeric(r.get("LATITUDE"))

        # Locality text: string prior to ',Jaipur'
        parts = addr.split(",")
        loc_text = parts[0].strip() if len(parts) > 1 else addr.strip()

        # Posted By
        pb_raw = str(r.get("POSTED_BY", "")).lower()
        if "owner" in pb_raw:
            posted_by = "owner"
        elif "builder" in pb_raw:
            posted_by = "builder"
        else:
            posted_by = "dealer"

        # RERA
        rera_num = parse_numeric(r.get("RERA"))
        rera_flag = bool(rera_num == 1) if rera_num is not None else None

        # Possession
        rtm_num = parse_numeric(r.get("READY_TO_MOVE"))
        possession = "ready_to_move" if rtm_num == 1 else "under_construction"

        # Property type
        type_str = str(r.get("BHK_OR_RK", "BHK")).upper()
        prop_type = "apartment" if "BHK" in type_str or "RK" in type_str else "other"

        rows.append(
            {
                "listing_id": make_listing_id("anmolkumar", idx),
                "source": "anmolkumar",
                "price_inr": price_inr,
                "area_sqft": float(area),
                "area_type": "Super Built-up Area",
                "bhk": bhk,
                "bathrooms": None,
                "property_type": prop_type,
                "locality_raw": loc_text,
                "locality_id": None,
                "lat": raw_lat,
                "lon": raw_lon,
                "coord_precision": "exact",
                "age_years": None,
                "floor": None,
                "total_floors": None,
                "furnishing": "unknown",
                "possession_status": possession,
                "posted_by": posted_by,
                "rera_flag": rera_flag,
                "listing_date": None,
            }
        )

    return pd.DataFrame(rows)


def ingest_all() -> pd.DataFrame:
    """Run full ingestion, concatenate sources, and save interim parquet."""
    raw_dir = DATA / "raw"
    interim_dir = DATA / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)

    kv_file = raw_dir / "karanveer_jaipur" / "flats_dataset.csv"
    ak_file = raw_dir / "anmolkumar" / "train.csv"

    print("Ingesting karanveer_jaipur...")
    df_kv = load_karanveer_raw(kv_file)
    print(f"Loaded {len(df_kv)} rows from karanveer_jaipur.")

    print("Ingesting anmolkumar...")
    df_ak = load_anmolkumar_raw(ak_file)
    print(f"Loaded {len(df_ak)} Jaipur rows from anmolkumar.")

    df_combined = pd.concat([df_kv, df_ak], ignore_index=True)
    df_combined = df_combined.sort_values("listing_id").reset_index(drop=True)

    out_file = interim_dir / "listings_std.parquet"
    df_combined.to_parquet(out_file, index=False)
    print(f"Saved {len(df_combined)} standardized listings to {out_file}.")
    return df_combined


if __name__ == "__main__":
    ingest_all()
