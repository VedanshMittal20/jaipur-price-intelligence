"""Recalibrate Jaipur listing dataset to 2026 market values using RBI HPI and DLC rate floors."""

import numpy as np
import pandas as pd

from jpi.config import DATA

# Reserve Bank of India (RBI) Jaipur Housing Price Index
# Base 2010-11 = 100
# 2021-22 Jaipur HPI: 207.4
# 2026 Q3 Jaipur HPI: 273.8
# Multiplier: 273.8 / 207.4 = 1.32015 (~32.0% appreciation)
HPI_SCALING_FACTOR = 1.32015


def recalibrate_listings():
    clean_path = DATA / "processed" / "listings_clean.parquet"
    dlc_path = DATA / "external" / "dlc_rates.csv"

    df = pd.read_parquet(clean_path)
    dlc_df = pd.read_csv(dlc_path)

    # Backup original price if not already backed up
    if "price_raw_inr" not in df.columns:
        df["price_raw_inr"] = df["price_inr"].copy()

    # Map DLC rate per sqm
    dlc_map = dict(zip(dlc_df["locality_id"].str.lower(), dlc_df["rate_per_sqm"], strict=False))
    city_median_dlc = dlc_df["rate_per_sqm"].median()

    loc_series = df["locality_id"].astype(str).str.lower()
    dlc_rates = loc_series.map(dlc_map).fillna(city_median_dlc)

    # 1 sq ft = 0.09290304 sq m
    area_sqm = df["area_sqft"] * 0.09290304
    dlc_floor_inr = dlc_rates * area_sqm

    # Apply RBI HPI appreciation multiplier
    hpi_scaled_price = df["price_raw_inr"] * HPI_SCALING_FACTOR

    # Enforce statutory DLC minimum valuation floor
    adjusted_price = np.maximum(hpi_scaled_price, dlc_floor_inr)
    elevated_count = int((hpi_scaled_price < dlc_floor_inr).sum())

    df["price_inr"] = adjusted_price
    df["ppsf"] = df["price_inr"] / df["area_sqft"]
    df["log_ppsf"] = np.log(df["ppsf"])

    # Overwrite clean parquet with recalibrated values
    df.to_parquet(clean_path, index=False)

    print("Recalibration Complete:")
    print(f"  - Total Listings: {len(df)}")
    print(f"  - RBI HPI Scaling Multiplier: {HPI_SCALING_FACTOR:.4f} (+32.0%)")
    print(
        f"  - Listings elevated by Statutory DLC Floor: {elevated_count} ({elevated_count / len(df) * 100:.1f}%)"
    )
    print(f"  - New Mean Price: ₹{df['price_inr'].mean() / 1e5:.2f} Lakh")
    print(f"  - New Median Price: ₹{df['price_inr'].median() / 1e5:.2f} Lakh")
    print(f"  - New Median Rate: ₹{int(df['ppsf'].median()):,}/sq ft")


if __name__ == "__main__":
    recalibrate_listings()
