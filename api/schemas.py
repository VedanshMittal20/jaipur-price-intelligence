"""Pydantic schemas for the Jaipur Price Intelligence API."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from jpi.config import JAIPUR_BBOX


class PropertyRequest(BaseModel):
    """Input parameters for a single Jaipur property price estimation."""

    area_sqft: float = Field(
        ..., ge=100.0, le=20000.0, description="Total built-up/super area in square feet"
    )
    bhk: int = Field(..., ge=1, le=10, description="Number of bedrooms (BHK)")
    bathrooms: Optional[float] = Field(None, ge=1.0, le=12.0, description="Number of bathrooms")
    floor: Optional[int] = Field(1, ge=0, le=60, description="Floor level (0 = ground)")
    total_floors: Optional[int] = Field(
        4, ge=1, le=60, description="Total number of floors in building"
    )
    property_type: str = Field("Apartment", description="Property type")
    furnishing: str = Field("Semi-Furnished", description="Furnishing state")
    possession_status: str = Field("Ready to Move", description="Possession readiness")
    posted_by: str = Field("Owner", description="Listing poster identity")
    rera_flag: int = Field(1, ge=0, le=1, description="1 if RERA approved/registered, 0 otherwise")
    locality: Optional[str] = Field(None, description="Jaipur locality / neighborhood name")
    lat: Optional[float] = Field(None, description="WGS84 Latitude")
    lon: Optional[float] = Field(None, description="WGS84 Longitude")

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            min_lat, _, max_lat, _ = JAIPUR_BBOX
            if not (min_lat <= v <= max_lat):
                raise ValueError(
                    f"Latitude {v:.5f} is outside Jaipur bounding box [{min_lat}, {max_lat}]"
                )
        return v

    @field_validator("lon")
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            _, min_lon, _, max_lon = JAIPUR_BBOX
            if not (min_lon <= v <= max_lon):
                raise ValueError(
                    f"Longitude {v:.5f} is outside Jaipur bounding box [{min_lon}, {max_lon}]"
                )
        return v


class FeatureFactor(BaseModel):
    """Individual feature factor impact."""

    feature: str
    label: str
    factor: float
    effect_pct: float
    direction: str  # 'positive' or 'negative'


class GroupFactor(BaseModel):
    """Aggregate group factor impact."""

    group: str
    factor: float
    effect_pct: float
    direction: str  # 'positive' or 'negative'


class CounterfactualScenario(BaseModel):
    """Estimated value shift under a hypothetical property modification."""

    scenario_id: str
    title: str
    description: str
    new_estimate_inr: float
    new_estimate_ppsf: float
    delta_inr: float
    delta_pct: float


class CounterfactualResponse(BaseModel):
    """Collection of what-if counterfactual scenario valuations."""

    baseline_estimate_inr: float
    scenarios: List[CounterfactualScenario]


class PricePredictionResponse(BaseModel):
    """Complete price intelligence estimate with calibrated interval and exact factor breakdown."""

    estimate_inr: float
    estimate_ppsf: float
    interval_low_inr: float
    interval_high_inr: float
    interval_low_ppsf: float
    interval_high_ppsf: float
    nominal_coverage: float = 0.80
    typical_price_inr: float
    locality: str
    lat: float
    lon: float
    coord_precision: str
    dlc_rate_per_sqm: Optional[float] = None
    factors: List[FeatureFactor]
    groups: List[GroupFactor]


class LocalitySummary(BaseModel):
    """Micro-market locality profile and baseline statistics."""

    locality_id: str
    name: str
    lat: float
    lon: float
    median_price_inr: float
    median_ppsf: float
    listing_count: int
    dlc_rate_per_sqm: Optional[float] = None
    dist_metro_km: Optional[float] = None


class LocalityInsightResponse(BaseModel):
    """Grounded micro-market intelligence narrative derived purely from computed statistics."""

    locality_id: str
    name: str
    tier: str
    median_price_inr: float
    median_ppsf: float
    listing_count: int
    dlc_rate_per_sqm: Optional[float] = None
    market_to_dlc_ratio: Optional[float] = None
    dist_metro_km: Optional[float] = None
    dist_primary_road_m: Optional[float] = None
    amenities_count_1000m: int
    narrative: str
    key_drivers: List[str]


class DealSummary(BaseModel):
    """Detected market listing priced below algorithmic fair valuation."""

    listing_id: str
    locality: str
    bhk: int
    area_sqft: float
    actual_price_inr: float
    actual_ppsf: float
    predicted_price_inr: float
    predicted_ppsf: float
    discount_pct: float
    lat: float
    lon: float


class ModelMetaResponse(BaseModel):
    """Metadata regarding served model weights, metrics, and training provenance."""

    model_name: str
    model_version: str
    trained_at: str
    features_count: int
    spatial_cv_mape: float
    test_mape: float
    test_r2: float
    nominal_coverage: float
    empirical_coverage: float
    container_ram_budget: str
