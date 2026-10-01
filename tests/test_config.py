"""Tests for central configuration and bounds."""

from jpi.config import (
    CITY_CENTER,
    INTERVAL_ALPHA,
    JAIPUR_BBOX,
    MAX_AREA_SQFT,
    MIN_AREA_SQFT,
    SEED,
    SPATIAL_BLOCK_DEG,
)


def test_config_constants():
    assert SEED == 42
    assert MIN_AREA_SQFT == 200.0
    assert MAX_AREA_SQFT == 20_000.0
    assert INTERVAL_ALPHA == 0.20
    assert SPATIAL_BLOCK_DEG == 0.02


def test_jaipur_bbox():
    south, west, north, east = JAIPUR_BBOX
    assert south < north
    assert west < east
    assert 26.0 < south < 27.5
    assert 75.0 < west < 77.0

    # City center should be inside bounding box
    lat, lon = CITY_CENTER
    assert south <= lat <= north
    assert west <= lon <= east
