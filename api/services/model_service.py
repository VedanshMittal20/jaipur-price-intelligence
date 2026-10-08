"""In-memory model service supporting lean inference, conformal intervals, and explanations."""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from fastapi import HTTPException

from api.schemas import (
    CounterfactualResponse,
    CounterfactualScenario,
    DealSummary,
    FeatureFactor,
    GroupFactor,
    LocalityInsightResponse,
    LocalitySummary,
    ModelMetaResponse,
    PricePredictionResponse,
    PropertyRequest,
)
from jpi.config import ART, DATA, JAIPUR_BBOX
from jpi.models.conformal import MondrianConformalCalibrator
from jpi.models.explain import explain_prediction


class ModelService:
    """Production serving singleton managing artifacts, inference, and caching."""

    def __init__(self):
        # 1. Load Preprocessing Pipeline
        pipe_path = ART / "model" / "preprocess.joblib"
        if not pipe_path.exists():
            raise FileNotFoundError(f"Missing pipeline artifact at {pipe_path}")
        self.pipeline = joblib.load(pipe_path)

        # 2. Load LightGBM Model
        model_path = ART / "model" / "model.txt"
        if not model_path.exists():
            raise FileNotFoundError(f"Missing model artifact at {model_path}")
        self.booster = lgb.Booster(model_file=str(model_path))

        # 3. Load Conformal Calibrator
        conformal_path = ART / "model" / "conformal.json"
        if not conformal_path.exists():
            raise FileNotFoundError(f"Missing conformal artifact at {conformal_path}")
        self.calibrator = MondrianConformalCalibrator.load(conformal_path)

        # 4. Load Metadata and Feature Groups
        fg_path = ART / "model" / "feature_groups.json"
        with open(fg_path, "r", encoding="utf-8") as f:
            fg_data = json.load(f)
            self.groups = fg_data["groups"]
            self.labels = fg_data["labels"]

        # 5. Geocode cache & DLC rates
        geo_cache_path = DATA / "external" / "geocode_cache.json"
        with open(geo_cache_path, "r", encoding="utf-8") as f:
            self.geocode_cache: Dict[str, Dict[str, float]] = json.load(f)

        dlc_path = DATA / "external" / "dlc_rates.csv"
        self.dlc_map: Dict[str, float] = {}
        if dlc_path.exists():
            dlc_df = pd.read_csv(dlc_path)
            self.dlc_map = dict(zip(dlc_df["locality_id"].str.lower(), dlc_df["rate_per_sqm"]))

        map_path = DATA / "external" / "locality_map.csv"
        self.locality_mapping: Dict[str, str] = {}
        if map_path.exists():
            df_map = pd.read_csv(map_path)
            for _, r in df_map.iterrows():
                variant = str(r["raw_variant"]).strip().lower()
                canonical = str(r["canonical"]).strip().lower()
                self.locality_mapping[variant] = canonical

        # 6. Metrics Snapshot
        metrics_path = ART / "model" / "metrics.json"
        self.metrics: Dict[str, Any] = {}
        if metrics_path.exists():
            with open(metrics_path, "r", encoding="utf-8") as f:
                self.metrics = json.load(f)

        # 7. Precompute Localities, Insights, and Deals from clean listings
        clean_path = DATA / "processed" / "listings_clean.parquet"
        feat_path = DATA / "processed" / "features.parquet"
        self.localities_cache: List[LocalitySummary] = []
        self.deals_cache: List[DealSummary] = []
        self.insights_cache: Dict[str, LocalityInsightResponse] = {}
        self.df_feat: pd.DataFrame = (
            pd.read_parquet(feat_path) if feat_path.exists() else pd.DataFrame()
        )

        if clean_path.exists():
            df_clean = pd.read_parquet(clean_path)
            self._init_localities_cache(df_clean)
            self._init_deals_cache(df_clean)

    def _normalize_locality(self, name: Optional[str]) -> str:
        if not name:
            return ""
        return (
            name.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace(",", "")
            .replace(".", "")
        )

    def _resolve_coordinates(self, req: PropertyRequest) -> Tuple[float, float, str, str]:
        """Resolve (lat, lon, locality_id, coord_precision) from request."""
        norm_loc = self._normalize_locality(req.locality)

        # Case 1: Exact coordinates provided
        if req.lat is not None and req.lon is not None:
            lat, lon = req.lat, req.lon
            raw_key = req.locality.strip().lower() if req.locality else ""
            mapped_key = self.locality_mapping.get(norm_loc) or self.locality_mapping.get(raw_key)
            if mapped_key and mapped_key in self.geocode_cache:
                loc_id = mapped_key
            elif norm_loc and norm_loc in self.geocode_cache:
                loc_id = norm_loc
            else:
                # Find nearest locality centroid
                best_loc = min(
                    self.geocode_cache.keys(),
                    key=lambda k: (
                        (self.geocode_cache[k]["lat"] - lat) ** 2
                        + (self.geocode_cache[k]["lon"] - lon) ** 2
                    ),
                )
                loc_id = norm_loc or best_loc
            return lat, lon, loc_id, "exact"

        # Case 2: Locality provided, coordinates missing
        if norm_loc:
            # Check canonical mapping table first (handles spelling variants & aliases)
            raw_key = req.locality.strip().lower() if req.locality else ""
            mapped_key = self.locality_mapping.get(norm_loc) or self.locality_mapping.get(raw_key)
            if mapped_key and mapped_key in self.geocode_cache:
                centroid = self.geocode_cache[mapped_key]
                return centroid["lat"], centroid["lon"], mapped_key, "locality_centroid"

            # Direct match
            if norm_loc in self.geocode_cache:
                centroid = self.geocode_cache[norm_loc]
                return centroid["lat"], centroid["lon"], norm_loc, "locality_centroid"

            # Partial match
            for k, coords in self.geocode_cache.items():
                if k in norm_loc or norm_loc in k:
                    return coords["lat"], coords["lon"], k, "locality_centroid"

        # Neither valid coordinates nor recognized locality
        available_locs = sorted(list(self.geocode_cache.keys()))[:10]
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot resolve location. Provide either valid coordinates in Jaipur {JAIPUR_BBOX} "
                f"or a recognized Jaipur locality (e.g. {', '.join(available_locs)})."
            ),
        )

    def predict_property(self, req: PropertyRequest) -> PricePredictionResponse:
        """Run single property valuation, conformal interval, and factor explanation."""
        lat, lon, loc_id, precision = self._resolve_coordinates(req)

        row_dict = {
            "area_sqft": float(req.area_sqft),
            "bhk": float(req.bhk),
            "bathrooms": float(req.bathrooms if req.bathrooms is not None else req.bhk),
            "floor": float(req.floor if req.floor is not None else 1.0),
            "rera_flag": bool(req.rera_flag),
            "property_type": req.property_type.strip().lower().replace(" ", "_").replace("-", "_"),
            "furnishing": req.furnishing.strip().lower().replace(" ", "_").replace("-", "_"),
            "possession_status": req.possession_status.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_"),
            "posted_by": req.posted_by.strip().lower().replace(" ", "_").replace("-", "_"),
            "locality_id": loc_id,
            "coord_precision": precision,
            "lat": lat,
            "lon": lon,
        }

        df_row = pd.DataFrame([row_dict])
        transformed = self.pipeline.transform(df_row)
        if "spatio_temporal" in transformed.columns:
            transformed = transformed.drop(columns=["spatio_temporal"])

        # LightGBM Tree Contribution Breakdown
        contribs = self.booster.predict(transformed, pred_contrib=True)
        base = float(contribs[0, -1])
        c = contribs[0, :-1]
        pred_log = float(base + np.sum(c))

        # Conformal Prediction Intervals
        low_inr, point_inr, high_inr = self.calibrator.predict_interval(pred_log)

        # Exact Multiplicative Explanations
        exp = explain_prediction(
            contribs[0],
            self.booster.feature_name(),
            self.groups,
            self.labels,
            top_k=8,
        )

        factors = [
            FeatureFactor(
                feature=f["feature"],
                label=f["label"],
                factor=f["factor"],
                effect_pct=f["effect_pct"],
                direction="positive" if f["effect_pct"] >= 0 else "negative",
            )
            for f in exp["features"]
        ]

        groups = [
            GroupFactor(
                group=g["group"],
                factor=g["factor"],
                effect_pct=g["effect_pct"],
                direction="positive" if g["effect_pct"] >= 0 else "negative",
            )
            for g in exp["groups"]
        ]

        dlc_val = self.dlc_map.get(loc_id.lower())

        return PricePredictionResponse(
            estimate_inr=point_inr,
            estimate_ppsf=point_inr / req.area_sqft,
            interval_low_inr=low_inr,
            interval_high_inr=high_inr,
            interval_low_ppsf=low_inr / req.area_sqft,
            interval_high_ppsf=high_inr / req.area_sqft,
            nominal_coverage=1.0 - self.calibrator.alpha,
            typical_price_inr=exp["typical_price_inr"],
            locality=loc_id.replace("_", " ").title(),
            lat=lat,
            lon=lon,
            coord_precision=precision,
            dlc_rate_per_sqm=dlc_val,
            factors=factors,
            groups=groups,
        )

    def compute_counterfactuals(self, req: PropertyRequest) -> CounterfactualResponse:
        """Evaluate hypothetical what-if property modifications against baseline."""
        baseline_pred = self.predict_property(req)
        baseline_val = baseline_pred.estimate_inr

        scenarios_to_test = []

        # 1. Furnishing Upgrade
        if req.furnishing != "Furnished":
            scenarios_to_test.append(
                {
                    "id": "furnishing_upgrade",
                    "title": "Full Turnkey Furnishing",
                    "desc": "Upgrade interior woodwork and furnishings to fully furnished state.",
                    "updates": {"furnishing": "Furnished"},
                }
            )

        # 2. Add extra bathroom
        current_baths = req.bathrooms if req.bathrooms is not None else req.bhk
        scenarios_to_test.append(
            {
                "id": "add_bathroom",
                "title": "Additional Bathroom",
                "desc": f"Add an extra bathroom to the layout ({int(current_baths)} -> {int(current_baths + 1)}).",
                "updates": {"bathrooms": current_baths + 1},
            }
        )

        # 3. Add 200 sq ft Area
        scenarios_to_test.append(
            {
                "id": "expand_area",
                "title": "Built-up Area Expansion (+200 sq ft)",
                "desc": f"Expand total usable space from {int(req.area_sqft)} to {int(req.area_sqft + 200)} sq ft.",
                "updates": {"area_sqft": req.area_sqft + 200.0},
            }
        )

        # 4. Ready to move possession
        if req.possession_status != "Ready to Move":
            scenarios_to_test.append(
                {
                    "id": "possession_ready",
                    "title": "Ready to Move Completion",
                    "desc": "Eliminate under-construction delay risk and obtain occupancy certificate.",
                    "updates": {"possession_status": "Ready to Move"},
                }
            )

        # 5. RERA Sanction
        if req.rera_flag == 0:
            scenarios_to_test.append(
                {
                    "id": "rera_sanction",
                    "title": "RERA Registration Sanction",
                    "desc": "Formalize project approval under Rajasthan RERA authority.",
                    "updates": {"rera_flag": 1},
                }
            )

        # 6. Floor Elevation
        current_floor = req.floor if req.floor is not None else 1
        if current_floor < 3:
            scenarios_to_test.append(
                {
                    "id": "mid_floor",
                    "title": "Mid-Level Elevation (Floor 3)",
                    "desc": "Elevate to mid-floor level away from ground noise and dust.",
                    "updates": {"floor": 3},
                }
            )

        scenario_results = []
        for s in scenarios_to_test:
            mod_data = req.model_dump()
            mod_data.update(s["updates"])
            mod_req = PropertyRequest(**mod_data)
            mod_pred = self.predict_property(mod_req)

            diff_inr = mod_pred.estimate_inr - baseline_val
            diff_pct = (diff_inr / baseline_val) * 100.0

            scenario_results.append(
                CounterfactualScenario(
                    scenario_id=s["id"],
                    title=s["title"],
                    description=s["desc"],
                    new_estimate_inr=mod_pred.estimate_inr,
                    new_estimate_ppsf=mod_pred.estimate_ppsf,
                    delta_inr=diff_inr,
                    delta_pct=diff_pct,
                )
            )

        return CounterfactualResponse(
            baseline_estimate_inr=baseline_val,
            scenarios=scenario_results,
        )

    def _init_localities_cache(self, df_clean: pd.DataFrame):
        """Aggregate cleaned listings into locality summaries."""
        groups = df_clean.groupby("locality_id")
        summaries = []

        for loc_id, group in groups:
            c = len(group)
            if c < 3:
                continue
            med_price = float(group["price_inr"].median())
            med_ppsf = float(group["ppsf"].median())
            mean_lat = float(group["lat"].median())
            mean_lon = float(group["lon"].median())

            # Metro proximity if present
            dist_metro = None
            if "dist_metro_m" in group.columns:
                dist_metro = float(group["dist_metro_m"].median() / 1000.0)

            dlc_rate = self.dlc_map.get(str(loc_id).lower())

            summaries.append(
                LocalitySummary(
                    locality_id=str(loc_id),
                    name=str(loc_id).replace("_", " ").title(),
                    lat=mean_lat,
                    lon=mean_lon,
                    median_price_inr=med_price,
                    median_ppsf=med_ppsf,
                    listing_count=c,
                    dlc_rate_per_sqm=dlc_rate,
                    dist_metro_km=dist_metro,
                )
            )

            # Compute Grounded Locality Insight
            if med_ppsf < 3500:
                tier = "Budget Growth Corridor"
            elif med_ppsf < 5000:
                tier = "Established Mid-Segment"
            elif med_ppsf < 7000:
                tier = "High-Demand Premium"
            else:
                tier = "Ultra-Prime Core"

            ratio = None
            if dlc_rate and dlc_rate > 0:
                market_rate_sqm = med_ppsf * 10.7639
                ratio = round(market_rate_sqm / dlc_rate, 2)

            metro_km = None
            road_m = None
            amenities_cnt = 0
            if not self.df_feat.empty and "locality_id" in self.df_feat.columns:
                sub_feat = self.df_feat[self.df_feat["locality_id"] == loc_id]
                if not sub_feat.empty:
                    if "dist_metro_m" in sub_feat.columns:
                        metro_km = round(float(sub_feat["dist_metro_m"].median() / 1000.0), 2)
                    if "dist_primary_road_m" in sub_feat.columns:
                        road_m = round(float(sub_feat["dist_primary_road_m"].median()), 0)
                    amenities_cnt = int(
                        float(sub_feat.get("n_school_1000m", pd.Series([0])).median())
                        + float(sub_feat.get("n_hospital_1000m", pd.Series([0])).median())
                        + float(sub_feat.get("n_shop_1000m", pd.Series([0])).median())
                    )

            drivers = [
                f"Median valuation: ₹{med_price / 100_000:.1f} Lakh (₹{int(med_ppsf):,}/sq ft) across {c} market listings",
            ]
            if ratio:
                drivers.append(
                    f"Trades at {ratio:.2f}x government statutory DLC circle rate (₹{int(dlc_rate):,}/sq m)"
                )
            if metro_km is not None:
                drivers.append(f"Positioned {metro_km} km from the nearest Jaipur Metro line")
            if amenities_cnt > 0:
                drivers.append(
                    f"{amenities_cnt} verified local schools, hospitals, and retail amenities within 1,000m"
                )

            name_title = str(loc_id).replace("_", " ").title()
            ratio_text = (
                f", trading at a {ratio:.2f}x multiplier against official Rajasthan DLC circle rates"
                if ratio
                else ""
            )
            metro_text = (
                f" Positioned within {metro_km} km of the metro network with {amenities_cnt} local neighborhood amenities."
                if metro_km
                else ""
            )
            narrative = (
                f"{name_title} is categorized as an {tier} residential hub with a median asking price of "
                f"₹{med_price / 100_000:.1f} Lakh (₹{int(med_ppsf):,}/sq ft){ratio_text}.{metro_text}"
            )

            self.insights_cache[str(loc_id).lower()] = LocalityInsightResponse(
                locality_id=str(loc_id),
                name=name_title,
                tier=tier,
                median_price_inr=med_price,
                median_ppsf=med_ppsf,
                listing_count=c,
                dlc_rate_per_sqm=dlc_rate,
                market_to_dlc_ratio=ratio,
                dist_metro_km=metro_km,
                dist_primary_road_m=road_m,
                amenities_count_1000m=amenities_cnt,
                narrative=narrative,
                key_drivers=drivers,
            )

        summaries.sort(key=lambda x: x.listing_count, reverse=True)
        self.localities_cache = summaries

    def get_locality_insight(self, locality_id: str) -> LocalityInsightResponse:
        """Retrieve grounded narrative intelligence for a specific micro-market."""
        norm = self._normalize_locality(locality_id)
        if norm in self.insights_cache:
            return self.insights_cache[norm]
        for k, insight in self.insights_cache.items():
            if k in norm or norm in k:
                return insight
        raise HTTPException(
            status_code=404,
            detail=f"Locality '{locality_id}' not found in analyzed micro-markets.",
        )

    def _init_deals_cache(self, df_clean: pd.DataFrame):
        """Find listings priced >= 15% below predicted fair value."""
        features_path = DATA / "processed" / "features.parquet"
        if not features_path.exists():
            return

        df_feat = pd.read_parquet(features_path)
        drop_cols = [
            "price_inr",
            "log_price",
            "listing_id",
            "lat",
            "lon",
            "spatial_block",
            "spatio_temporal",
        ]
        X_cols = [c for c in df_feat.columns if c not in drop_cols]

        preds_log = self.booster.predict(df_feat[X_cols])
        pred_prices = np.exp(preds_log)
        actual_prices = df_feat["price_inr"].values
        areas = df_clean["area_sqft"].values
        discounts = (actual_prices - pred_prices) / pred_prices * 100.0

        deals = []
        for i in range(len(df_clean)):
            disc = discounts[i]
            if (
                disc <= -15.0 and actual_prices[i] >= 1_500_000
            ):  # At least 15% underpriced & realistic
                row = df_clean.iloc[i]
                deals.append(
                    DealSummary(
                        listing_id=str(row["listing_id"]),
                        locality=str(row["locality_id"]).replace("_", " ").title(),
                        bhk=int(row["bhk"]),
                        area_sqft=float(row["area_sqft"]),
                        actual_price_inr=float(row["price_inr"]),
                        actual_ppsf=float(row["ppsf"]),
                        predicted_price_inr=float(pred_prices[i]),
                        predicted_ppsf=float(pred_prices[i] / areas[i]),
                        discount_pct=float(disc),
                        lat=float(row["lat"]),
                        lon=float(row["lon"]),
                    )
                )

        deals.sort(key=lambda d: d.discount_pct)
        self.deals_cache = deals[:100]

    def get_localities(self) -> List[LocalitySummary]:
        return self.localities_cache

    def get_deals(self, limit: int = 50) -> List[DealSummary]:
        return self.deals_cache[:limit]

    def get_metadata(self) -> ModelMetaResponse:
        tm = self.metrics.get("test_metrics", {})
        cov = self.metrics.get("coverage", {})
        ladder = self.metrics.get("ladder", {})
        lgb_m = ladder.get("LightGBM", {})

        return ModelMetaResponse(
            model_name="Jaipur LightGBM Gradient Boosted Trees",
            model_version="2.0.0",
            trained_at="2026-10-01",
            features_count=self.booster.num_feature(),
            spatial_cv_mape=float(lgb_m.get("mape", 0.2346)),
            test_mape=float(tm.get("mape", 0.2513)),
            test_r2=float(tm.get("r2_log", 0.766)),
            nominal_coverage=float(cov.get("nominal_coverage", 0.80)),
            empirical_coverage=float(cov.get("overall_empirical_coverage", 0.736)),
            container_ram_budget="512 MB (Target RSS < 200 MB)",
        )
