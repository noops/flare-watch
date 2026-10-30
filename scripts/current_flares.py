"""The actually-current companion to analyze.py's historical (2019-2021)
analysis: maps and attributes the last 5 days of real VIIRS detections.

Run scripts/fetch_firms.py first to refresh the data, then this.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import nearest_well_operator, MAX_MATCH_KM  # noqa: E402
from mapping import plot_texas_detections  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
RESULTS_DIR = ROOT / "results"


def main() -> None:
    detections = pd.read_csv(RAW_DIR / "tx_firms_current.csv")
    wells = pd.read_csv(RAW_DIR / "tx_wells.csv").dropna(subset=["latitude_surface_hole", "longitude_surface_hole"])

    # current_flares.py's columns (from FIRMS) use lat/lon names different
    # from analyze.py's VIIRS-mirror columns (lat_gmtco/lon_gmtco) —
    # nearest_well_operator expects the latter, so rename for reuse.
    detections = detections.rename(columns={"latitude": "lat_gmtco", "longitude": "lon_gmtco"})

    date_range = f"{detections['acq_date'].min()} to {detections['acq_date'].max()}"
    print(f"{len(detections):,} current Texas nighttime detections ({date_range})")

    operator, dist_km = nearest_well_operator(detections, wells)
    detections["nearest_operator"] = operator
    matched_pct = (dist_km <= MAX_MATCH_KM).mean()
    print(f"{matched_pct:.1%} matched to a well within {MAX_MATCH_KM}km")

    leaderboard = (
        detections[detections["nearest_operator"] != "(no well within 2km)"]
        .groupby("nearest_operator")
        .size()
        .sort_values(ascending=False)
        .head(15)
    )
    print(f"\nTop operators by nearby current detections ({date_range}):")
    print(leaderboard.to_string())

    RESULTS_DIR.mkdir(exist_ok=True)
    leaderboard.to_csv(RESULTS_DIR / "current_top_operators.csv")

    plot_texas_detections(
        detections["lon_gmtco"], detections["lat_gmtco"],
        title=f"{len(detections):,} current VIIRS nighttime thermal detections, Texas ({date_range})",
        out_path=RESULTS_DIR / "current_detection_map.png",
        color="orangered",
    )
    print(f"\nSaved {RESULTS_DIR / 'current_detection_map.png'} and {RESULTS_DIR / 'current_top_operators.csv'}")


if __name__ == "__main__":
    main()
