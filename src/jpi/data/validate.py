"""Data contract and schema validation using Pandera."""

from pathlib import Path
from typing import Optional

import pandas as pd
import pandera as pa

from jpi.config import DATA, MAX_AREA_SQFT, MIN_AREA_SQFT

clean_listing_schema = pa.DataFrameSchema(
    {
        "listing_id": pa.Column(str, unique=True),
        "source": pa.Column(str, pa.Check.isin(["karanveer_jaipur", "anmolkumar"])),
        "price_inr": pa.Column(float, pa.Check.gt(0)),
        "area_sqft": pa.Column(float, pa.Check.in_range(MIN_AREA_SQFT, MAX_AREA_SQFT)),
        "bhk": pa.Column(int, pa.Check.in_range(1, 10)),
        "bathrooms": pa.Column(float, nullable=True),
        "property_type": pa.Column(
            str,
            pa.Check.isin(["apartment", "independent_house", "villa", "builder_floor", "other"]),
        ),
        "locality_id": pa.Column(str, nullable=False),
        "lat": pa.Column(float, nullable=False),
        "lon": pa.Column(float, nullable=False),
        "coord_precision": pa.Column(str, pa.Check.isin(["exact", "locality_centroid"])),
    },
    strict=False,
    coerce=True,
)


def validate_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Validate DataFrame against canonical clean schema and assert quality checks."""
    # Assert no personal-data columns exist BEFORE schema validation
    banned_cols = [
        "name",
        "owner_name",
        "phone",
        "email",
        "contact",
        "address",
        "property_link",
        "property_description",
    ]
    for col in df.columns:
        assert col.lower() not in banned_cols, f"Security Violation: PII column '{col}' detected!"

    validated = clean_listing_schema.validate(df)

    # Assert coordinate coverage
    valid_coords = df["lat"].notna() & df["lon"].notna()
    coord_pct = valid_coords.mean() * 100.0
    assert coord_pct >= 60.0, f"Coordinate coverage too low: {coord_pct:.1f}% (required >= 60%)"

    return validated


def validate_clean_parquet(file_path: Optional[Path] = None) -> pd.DataFrame:
    """Load and validate clean parquet file."""
    if file_path is None:
        file_path = DATA / "processed" / "listings_clean.parquet"
    if not file_path.exists():
        raise FileNotFoundError(f"Clean parquet not found at {file_path}")
    df = pd.read_parquet(file_path)
    return validate_dataset(df)


if __name__ == "__main__":
    df = validate_clean_parquet()
    print(f"Validation successful! {len(df)} rows verified against pandera schema.")
