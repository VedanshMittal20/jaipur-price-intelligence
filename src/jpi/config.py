"""Central configuration, bounding boxes, and hyperparameter constants."""

from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
ART = ROOT / "artifacts"

# Jaipur Metropolitan Bounding Box (south, west, north, east)
# Latitude: 26.55 N to 27.15 N
# Longitude: 75.50 E to 76.15 E
JAIPUR_BBOX = (26.55, 75.50, 27.15, 76.15)
CITY_CENTER = (26.9124, 75.7873)  # Approximate Jaipur city center

# Data validation bounds
MIN_AREA_SQFT = 200.0
MAX_AREA_SQFT = 20_000.0

MIN_PPSF = 1_000.0  # ₹ / sq ft minimum flag threshold
MAX_PPSF = 30_000.0  # ₹ / sq ft maximum flag threshold

# Spatial cross-validation block resolution (~2.2 km per block)
SPATIAL_BLOCK_DEG = 0.02

# Conformal prediction interval significance (80% coverage intervals)
INTERVAL_ALPHA = 0.20
