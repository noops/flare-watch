"""Pull VIIRS Nightfire flare-detection data, Texas well locations, and
Texas state-reported flaring volumes — all public, no registration.

VIIRS is the imaging instrument on NASA/NOAA satellites; Nightfire is
the detection algorithm that turns VIIRS data into actual flare
locations and radiant heat, developed by the Earth Observation Group
(EOG) at the Colorado School of Mines — not a NASA/NOAA product.

Source: flaringmonitor/viirs-flare-data on GitHub, which mirrors EOG's
Nightfire output alongside cleaned well/operator metadata from state
regulators. EOG's own site (eogdata.mines.edu) requires a free account;
this mirror doesn't, so it's the actual no-signup public entry point.

Texas filtering uses a real polygon (via states.csv.gz's geometry), not a
lat/lon bounding box — Texas and New Mexico share a border right through
the Permian Basin, where most of this flaring happens, so a bounding box
would misattribute New Mexico detections to Texas.
"""

import gzip
import io
from pathlib import Path

import pandas as pd
import requests
from shapely import wkb
from shapely.geometry import Point

BASE_URL = "https://raw.githubusercontent.com/flaringmonitor/viirs-flare-data/main/raw/"
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
CACHE_DIR = RAW_DIR / "_cache"


def fetch_gz_csv(name: str) -> pd.DataFrame:
    cache_path = CACHE_DIR / name.replace(".gz", "")
    if cache_path.exists():
        return pd.read_csv(cache_path)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    resp = requests.get(BASE_URL + name, timeout=120)
    resp.raise_for_status()
    df = pd.read_csv(io.BytesIO(resp.content), compression="gzip")
    df.to_csv(cache_path, index=False)
    return df


def texas_polygon():
    states = fetch_gz_csv("states.csv.gz")
    tx_hex = states.loc[states["state_abbr"] == "TX", "geom"].iloc[0]
    return wkb.loads(bytes.fromhex(tx_hex))


def main() -> None:
    print("Fetching VIIRS satellite flare detections (4 states, 2019+)...")
    viirs = fetch_gz_csv("viirs.csv.gz")
    print(f"  {len(viirs):,} total detections across ND/NM/TX/CO")

    print("Fetching Texas polygon and filtering detections to Texas...")
    tx_poly = texas_polygon()
    # Prefilter with a bounding box first (cheap), then exact polygon test
    # only on the much smaller candidate set (expensive .contains() call).
    minx, miny, maxx, maxy = tx_poly.bounds
    candidates = viirs[
        (viirs["lon_gmtco"] >= minx) & (viirs["lon_gmtco"] <= maxx)
        & (viirs["lat_gmtco"] >= miny) & (viirs["lat_gmtco"] <= maxy)
    ].copy()
    in_tx = candidates.apply(lambda r: tx_poly.contains(Point(r["lon_gmtco"], r["lat_gmtco"])), axis=1)
    tx_viirs = candidates[in_tx].reset_index(drop=True)
    print(f"  {len(tx_viirs):,} detections actually inside Texas "
          f"({len(candidates) - len(tx_viirs):,} in the bounding box but across the NM border, excluded)")

    print("Fetching well locations and filtering to Texas...")
    wells = fetch_gz_csv("flare_wells.csv.gz")
    tx_wells = wells[wells["state"] == "TX"].reset_index(drop=True)
    print(f"  {len(tx_wells):,} Texas wells")

    print("Fetching state-reported flaring volumes and filtering to Texas...")
    reported = fetch_gz_csv("reported_flares.csv.gz")
    tx_reported = reported[reported["state"] == "TX"].reset_index(drop=True)
    print(f"  {len(tx_reported):,} Texas reported-flaring records")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tx_viirs.to_csv(RAW_DIR / "tx_viirs_detections.csv", index=False)
    tx_wells.to_csv(RAW_DIR / "tx_wells.csv", index=False)
    tx_reported.to_csv(RAW_DIR / "tx_reported_flares.csv", index=False)
    print(f"\nSaved Texas-filtered data to {RAW_DIR}")


if __name__ == "__main__":
    main()
