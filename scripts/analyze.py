"""Texas flare detections: where they are, how they've trended since
2019, and which operators' wells they're nearest to.

The operator attribution is a nearest-well spatial join (BallTree,
haversine distance), not a legal claim — a detection near a well doesn't
prove that well caused it (flares can be miles from the wellhead, multiple
wells cluster together, and satellite geolocation has its own error).
Treat it as "closest named operator," a reasonable first filter, not
a citation.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.neighbors import BallTree

MAX_MATCH_KM = 2.0  # don't attribute a detection to a well more than this far away

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
RESULTS_DIR = ROOT / "results"


def nearest_well_operator(detections: pd.DataFrame, wells: pd.DataFrame) -> pd.Series:
    well_coords = np.radians(wells[["latitude_surface_hole", "longitude_surface_hole"]].to_numpy())
    tree = BallTree(well_coords, metric="haversine")

    det_coords = np.radians(detections[["lat_gmtco", "lon_gmtco"]].to_numpy())
    dist, idx = tree.query(det_coords, k=1)
    dist_km = dist.flatten() * 6371.0  # earth radius

    operator = wells["operator_name"].to_numpy()[idx.flatten()]
    operator = np.where(dist_km <= MAX_MATCH_KM, operator, "(no well within 2km)")
    return pd.Series(operator, index=detections.index), dist_km


def main() -> None:
    detections = pd.read_csv(RAW_DIR / "tx_viirs_detections.csv", parse_dates=["date_ltz"])
    wells = pd.read_csv(RAW_DIR / "tx_wells.csv").dropna(subset=["latitude_surface_hole", "longitude_surface_hole"])
    reported = pd.read_csv(RAW_DIR / "tx_reported_flares.csv", parse_dates=["month"])

    print(f"{len(detections):,} Texas detections, {len(wells):,} Texas wells with coordinates")

    # --- Monthly detection trend ---
    # Drop the last calendar month if the data doesn't fully cover it —
    # a partial month otherwise shows up as a misleading dip to near-zero.
    last_full_month = detections["date_ltz"].max().to_period("M") - 1

    detections["month"] = detections["date_ltz"].dt.to_period("M")
    monthly_detections = detections[detections["month"] <= last_full_month].groupby("month").size()
    reported_month = reported["month"].dt.to_period("M")
    monthly_reported = reported[reported_month <= last_full_month].groupby(reported_month[reported_month <= last_full_month])["flared"].sum()

    RESULTS_DIR.mkdir(exist_ok=True)
    fig, ax1 = plt.subplots(figsize=(10, 4.5))
    ax1.plot(monthly_detections.index.to_timestamp(), monthly_detections.values, color="tab:red", label="Satellite detections (count)")
    ax1.set_ylabel("VIIRS flare detections / month", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")

    ax2 = ax1.twinx()
    ax2.plot(monthly_reported.index.to_timestamp(), monthly_reported.values, color="tab:blue", linestyle="--", label="State-reported volume")
    ax2.set_ylabel("State-reported flared volume / month", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    ax1.set_title("Texas flaring: satellite detections vs. state-reported volume (different units — trend comparison only)")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "monthly_trend.png", dpi=150)
    print(f"Saved {RESULTS_DIR / 'monthly_trend.png'}")

    # --- Map of detection density ---
    fig2, ax = plt.subplots(figsize=(7, 8))
    ax.scatter(detections["lon_gmtco"], detections["lat_gmtco"], s=0.5, alpha=0.15, color="tab:red")
    date_range = f"{detections['date_ltz'].min().strftime('%b %Y')}-{detections['date_ltz'].max().strftime('%b %Y')}"
    ax.set_title(f"{len(detections):,} VIIRS flare detections in Texas, {date_range}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    fig2.tight_layout()
    fig2.savefig(RESULTS_DIR / "detection_map.png", dpi=150)
    print(f"Saved {RESULTS_DIR / 'detection_map.png'}")

    # --- Nearest-well operator attribution ---
    print("Running nearest-well spatial join (BallTree, haversine)...")
    operator, dist_km = nearest_well_operator(detections, wells)
    detections["nearest_operator"] = operator
    detections["nearest_well_km"] = dist_km
    matched_pct = (dist_km <= MAX_MATCH_KM).mean()
    print(f"{matched_pct:.1%} of detections matched to a well within {MAX_MATCH_KM}km")

    leaderboard = (
        detections[detections["nearest_operator"] != "(no well within 2km)"]
        .groupby("nearest_operator")
        .size()
        .sort_values(ascending=False)
        .head(15)
    )
    print(f"\nTop 15 operators by nearby detected flares ({date_range}):")
    print(leaderboard.to_string())
    leaderboard.to_csv(RESULTS_DIR / "top_operators_by_detections.csv")
    detections.to_csv(RESULTS_DIR / "tx_detections_with_operator.csv", index=False)
    print(f"\nSaved {RESULTS_DIR / 'top_operators_by_detections.csv'} and full attributed detections")


if __name__ == "__main__":
    main()
