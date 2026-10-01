"""Download and extract Karan Veer's Jaipur Real Estate Property Dataset."""

import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

TARGET_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "karanveer_jaipur"
KAGGLE_API_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/karanveer59/real-estate-property-dataset"
)
EXPECTED_SHA256 = "232cc908b113d77e99b83ee3bce8119094744435b7c85264b29e7b80f3d73ab9"


def download():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    target_csv = TARGET_DIR / "flats_dataset.csv"

    if target_csv.exists():
        hasher = hashlib.sha256()
        with open(target_csv, "rb") as f:
            hasher.update(f.read())
        if hasher.hexdigest() == EXPECTED_SHA256:
            print(f"File {target_csv} already exists with verified checksum.")
            return

    print(f"Downloading from {KAGGLE_API_URL}...")
    req = urllib.request.Request(
        KAGGLE_API_URL, headers={"User-Agent": "JaipurPriceIntelligence/1.0"}
    )
    with urllib.request.urlopen(req) as response:
        content = response.read()

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        zf.extractall(TARGET_DIR)

    print(f"Extracted to {TARGET_DIR}")


if __name__ == "__main__":
    download()
