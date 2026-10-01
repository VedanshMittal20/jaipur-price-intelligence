"""Feature engineering pipeline, geospatial distance calculations, and serialization."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from jpi.config import ART, DATA
from jpi.geo.nearest import GeoLayers

DIST_LAYERS = [
    "metro",
    "rail",
    "airport",
    "primary_road",
    "hospital",
    "school",
    "mall",
    "park",
    "cbd",
]
COUNT_LAYERS = ["school", "hospital", "restaurant", "shop"]
RADII_M = (500, 1000, 2000)

CATEGORICAL_COLS = [
    "property_type",
    "furnishing",
    "possession_status",
    "posted_by",
    "coord_precision",
    "locality_id",
]

FEATURE_GROUPS = {
    "area_sqft": "Property characteristics",
    "bhk": "Property characteristics",
    "bathrooms": "Property characteristics",
    "bath_per_bhk": "Property characteristics",
    "floor": "Property characteristics",
    "rera_flag": "Property characteristics",
    "property_type": "Property characteristics",
    "furnishing": "Property characteristics",
    "possession_status": "Property characteristics",
    "posted_by": "Property characteristics",
    "dist_metro_m": "Connectivity",
    "dist_rail_m": "Connectivity",
    "dist_airport_m": "Connectivity",
    "dist_primary_road_m": "Connectivity",
    "dist_cbd_m": "Connectivity",
    "dist_hospital_m": "Neighbourhood amenities",
    "dist_school_m": "Neighbourhood amenities",
    "dist_mall_m": "Neighbourhood amenities",
    "dist_park_m": "Neighbourhood amenities",
    "n_school_1000m": "Neighbourhood amenities",
    "n_hospital_1000m": "Neighbourhood amenities",
    "n_restaurant_1000m": "Neighbourhood amenities",
    "n_shop_1000m": "Neighbourhood amenities",
    "locality_id": "Locality & market",
    "coord_precision": "Locality & market",
    "dlc_rate_per_sqm": "Locality & market",
    "dlc_missing": "Locality & market",
}

FEATURE_LABELS = {
    "area_sqft": "Total Area (sq ft)",
    "bhk": "Bedrooms (BHK)",
    "bathrooms": "Number of Bathrooms",
    "bath_per_bhk": "Bathroom to BHK Ratio",
    "floor": "Floor Level",
    "rera_flag": "RERA Approved Project",
    "property_type": "Property Category",
    "furnishing": "Furnishing Level",
    "possession_status": "Construction / Possession Status",
    "posted_by": "Listed By (Owner/Dealer/Builder)",
    "dist_metro_m": "Distance to Nearest Metro",
    "dist_rail_m": "Distance to Nearest Railway Station",
    "dist_airport_m": "Distance to Jaipur Airport",
    "dist_primary_road_m": "Distance to Major Highway",
    "dist_cbd_m": "Distance to City Commercial Hub",
    "dist_hospital_m": "Distance to Nearest Hospital",
    "dist_school_m": "Distance to Nearest School",
    "dist_mall_m": "Distance to Nearest Shopping Mall",
    "dist_park_m": "Distance to Nearest Public Park",
    "n_school_1000m": "Schools within 1 km",
    "n_hospital_1000m": "Hospitals within 1 km",
    "n_restaurant_1000m": "Restaurants within 1 km",
    "n_shop_1000m": "Retail Outlets within 1 km",
    "locality_id": "Locality Premium",
    "coord_precision": "Geocode Location Precision",
    "dlc_rate_per_sqm": "Government Circle Rate (DLC)",
    "dlc_missing": "Circle Rate Prior Available",
}


def load_dlc_table() -> pd.DataFrame:
    """Load DLC rates table."""
    dlc_path = DATA / "external" / "dlc_rates.csv"
    if dlc_path.exists():
        return pd.read_csv(dlc_path)
    return pd.DataFrame(columns=["locality_id", "rate_per_sqm"])


def compute_geo_distances(latlon: np.ndarray, layers: GeoLayers) -> pd.DataFrame:
    """Compute distances to nearest anchors and density counts within radii."""
    features = {}
    for layer in DIST_LAYERS:
        features[f"dist_{layer}_m"] = layers[layer].nearest_m(latlon)

    for layer in COUNT_LAYERS:
        for r in RADII_M:
            features[f"n_{layer}_{r}m"] = layers[layer].count_within(latlon, float(r))

    return pd.DataFrame(features)


class FeaturePipeline:
    """End-to-end scikit-learn compatible feature builder and preprocessor."""

    def __init__(self, geo_layers_path: Optional[Path] = None):
        if geo_layers_path is None:
            geo_layers_path = ART / "geo" / "geo_layers.npz"
        self.geo_layers = GeoLayers(geo_layers_path)
        self.categories_: Dict[str, List[str]] = {}
        self.dlc_map_: Dict[str, float] = {}
        self.feature_names_: List[str] = []

    def fit(self, df: pd.DataFrame, y=None):
        """Learn categorical vocabularies and DLC reference mapping."""
        # Load DLC map
        dlc_df = load_dlc_table()
        if not dlc_df.empty:
            self.dlc_map_ = dict(zip(dlc_df["locality_id"].str.lower(), dlc_df["rate_per_sqm"].astype(float)))

        # Learn categorical vocabularies
        for col in CATEGORICAL_COLS:
            vals = sorted(df[col].dropna().astype(str).unique().tolist())
            if "unknown" not in vals and col != "locality_id":
                vals.append("unknown")
            self.categories_[col] = vals

        # Save categorical metadata
        art_model = ART / "model"
        art_model.mkdir(parents=True, exist_ok=True)
        with open(art_model / "categories.json", "w", encoding="utf-8") as f:
            json.dump(self.categories_, f, indent=2)

        with open(art_model / "feature_groups.json", "w", encoding="utf-8") as f:
            json.dump({"groups": FEATURE_GROUPS, "labels": FEATURE_LABELS}, f, indent=2)

        # Fit transform on dummy to store feature names
        sample_transformed = self.transform(df.iloc[:2])
        self.feature_names_ = list(sample_transformed.columns)

        with open(art_model / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "feature_names": self.feature_names_,
                    "categorical_features": CATEGORICAL_COLS,
                    "target": "log_price",
                },
                f,
                indent=2,
            )

        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw listing DataFrame into model feature matrix."""
        df = df.copy()

        # 1. Structural property features
        out = pd.DataFrame(index=df.index)
        out["area_sqft"] = df["area_sqft"].astype(float)
        out["bhk"] = df["bhk"].astype(float)

        # Bathrooms
        baths = pd.to_numeric(df.get("bathrooms"), errors="coerce")
        out["bathrooms"] = baths.fillna(df["bhk"]).astype(float)
        out["bath_per_bhk"] = out["bathrooms"] / np.maximum(out["bhk"], 1.0)

        # Floor
        out["floor"] = pd.to_numeric(df.get("floor"), errors="coerce").fillna(1.0).astype(float)

        # RERA flag
        rera = df.get("rera_flag")
        out["rera_flag"] = rera.map({True: 1.0, False: 0.0}).fillna(0.0).astype(float)

        # 2. Geospatial features
        latlon = np.c_[df["lat"].values, df["lon"].values]
        geo_df = compute_geo_distances(latlon, self.geo_layers)
        for c in geo_df.columns:
            out[c] = geo_df[c].values

        # 3. DLC prior
        loc_ids = df["locality_id"].astype(str).str.lower()
        dlc_rates = loc_ids.map(self.dlc_map_)
        out["dlc_rate_per_sqm"] = dlc_rates.fillna(30000.0).astype(float)
        out["dlc_missing"] = dlc_rates.isna().astype(float)

        # 4. Categoricals: encode as integer category codes
        for col in CATEGORICAL_COLS:
            vocab = self.categories_.get(col, [])
            val_series = df[col].astype(str).str.lower().str.replace(" ", "_").str.replace("-", "_")
            cat_type = pd.CategoricalDtype(categories=vocab, ordered=False)
            out[col] = val_series.astype(cat_type).cat.codes.astype(int)

        return out


def build_and_save_features():
    """Build features from cleaned parquet and persist pipeline."""
    clean_path = DATA / "processed" / "listings_clean.parquet"
    df_clean = pd.read_parquet(clean_path)

    pipe = FeaturePipeline()
    pipe.fit(df_clean)

    X = pipe.transform(df_clean)
    y = np.log(df_clean["price_inr"].values)

    # Save preprocess pipeline
    joblib.dump(pipe, ART / "model" / "preprocess.joblib")

    # Save feature matrix
    X_with_target = X.copy()
    X_with_target["price_inr"] = df_clean["price_inr"].values
    X_with_target["log_price"] = y
    X_with_target["listing_id"] = df_clean["listing_id"].values
    X_with_target["lat"] = df_clean["lat"].values
    X_with_target["lon"] = df_clean["lon"].values

    out_file = DATA / "processed" / "features.parquet"
    X_with_target.to_parquet(out_file, index=False)

    print(f"Features created: {X.shape[1]} features for {X.shape[0]} rows saved to {out_file}.")
    print("Features:", list(X.columns))
    return pipe, X, y


if __name__ == "__main__":
    build_and_save_features()
