"""Unit tests for data normalization, cleaning, and schema validation."""

import numpy as np
import pandas as pd
import pytest

from jpi.data.clean import (
    deduplicate_listings,
    parse_area_to_sqft,
    parse_price_to_inr,
)
from jpi.data.validate import clean_listing_schema, validate_dataset


def test_unit_normalization_price():
    # 10+ test examples including edge cases
    assert parse_price_to_inr("1.2 Cr") == 12_000_000.0
    assert parse_price_to_inr("1.2Cr") == 12_000_000.0
    assert parse_price_to_inr("85 Lac") == 8_500_000.0
    assert parse_price_to_inr("85 lacs") == 8_500_000.0
    assert parse_price_to_inr("₹ 90,00,000") == 9_000_000.0
    assert parse_price_to_inr("50,00,000") == 5_000_000.0
    assert parse_price_to_inr("45.5 Lakh") == 4_550_000.0
    assert parse_price_to_inr("1.05 Crore") == 10_500_000.0
    assert parse_price_to_inr("95 L") == 9_500_000.0
    assert parse_price_to_inr("2.1 CR") == 21_000_000.0
    assert parse_price_to_inr("65.0") == 6_500_000.0  # Lakh representation
    assert parse_price_to_inr(7500000) == 7_500_000.0
    assert parse_price_to_inr(None) is None
    assert parse_price_to_inr("invalid") is None


def test_unit_normalization_area():
    # Square yards (1 sqyd = 9 sqft)
    assert parse_area_to_sqft("100 sq yd") == 900.0
    assert parse_area_to_sqft("150 sqyd") == 1350.0
    assert parse_area_to_sqft("200 gaj") == 1800.0

    # Square meters (1 sqm = 10.7639 sqft)
    assert pytest.approx(parse_area_to_sqft("100 sq m"), 0.1) == 1076.39
    assert pytest.approx(parse_area_to_sqft("50 sqm"), 0.1) == 538.195

    # Square feet standard
    assert parse_area_to_sqft("1200 sqft") == 1200.0
    assert parse_area_to_sqft("1,500 sq ft") == 1500.0
    assert parse_area_to_sqft(1850) == 1850.0
    assert parse_area_to_sqft(None) is None


def test_deduplication():
    df = pd.DataFrame(
        [
            {
                "source": "karanveer_jaipur",
                "price_inr": 5_000_000.0,
                "area_sqft": 1200.0,
                "bhk": 3,
                "locality_raw": "Mansarovar",
            },
            {
                "source": "karanveer_jaipur",
                "price_inr": 5_000_000.0,
                "area_sqft": 1200.0,
                "bhk": 3,
                "locality_raw": "Mansarovar",
            },
            {
                "source": "karanveer_jaipur",
                "price_inr": 6_000_000.0,
                "area_sqft": 1400.0,
                "bhk": 3,
                "locality_raw": "Vaishali Nagar",
            },
        ]
    )
    deduped, stats = deduplicate_listings(df)
    assert len(deduped) == 2
    assert stats["exact_duplicates_dropped"] == 1


def test_validation_schema_fixture():
    fixture = pd.DataFrame(
        [
            {
                "listing_id": "test_id_001",
                "source": "karanveer_jaipur",
                "price_inr": 5_500_000.0,
                "area_sqft": 1250.0,
                "bhk": 3,
                "bathrooms": 2.0,
                "property_type": "apartment",
                "locality_id": "mansarovar",
                "lat": 26.8533,
                "lon": 75.7607,
                "coord_precision": "exact",
            }
        ]
    )
    validated = validate_dataset(fixture)
    assert len(validated) == 1


def test_banned_pii_columns():
    df_with_pii = pd.DataFrame(
        [
            {
                "listing_id": "test_002",
                "source": "karanveer_jaipur",
                "price_inr": 4_000_000.0,
                "area_sqft": 1000.0,
                "bhk": 2,
                "property_type": "apartment",
                "locality_id": "jagatpura",
                "lat": 26.8220,
                "lon": 75.8390,
                "coord_precision": "exact",
                "owner_name": "John Doe",  # Banned PII
            }
        ]
    )
    with pytest.raises(AssertionError, match="Security Violation"):
        validate_dataset(df_with_pii)
