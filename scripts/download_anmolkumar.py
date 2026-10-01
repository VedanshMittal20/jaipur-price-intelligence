"""Download and extract Anmol Kumar's House Price Prediction Challenge Dataset."""

import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

TARGET_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "anmolkumar"
KAGGLE_API_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/anmolkumar/house-price-prediction-challenge"
)
EXPECTED_TRAIN_SHA256 = "b960388685fd0ce4e1935f4854fdf2256b556b7976b134d82aa4972525faa32b"


def download():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    train_csv = TARGET_DIR / "train.csv"

    if train_csv.exists():
        hasher = hashlib.sha256()
        with open(train_csv, "rb") as f:
            hasher.update(f.read())
        if hasher.hexdigest() == EXPECTED_TRAIN_SHA256:
            print(f"File {train_csv} already exists with verified checksum.")
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
