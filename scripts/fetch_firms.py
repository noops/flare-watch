"""Pull current VIIRS thermal-anomaly detections for Texas from NASA FIRMS
— a genuinely open alternative to EOG's licensed VIIRS Nightfire product.

FIRMS (Fire Information for Resource Management System) runs NASA's own
active-fire detection algorithm on the same VIIRS satellites Nightfire
uses, but with instant free API access (email signup, no institutional
license) instead of EOG's academic/commercial/non-profit license tiers.

Honest tradeoff: FIRMS is built for wildfires, not flares specifically.
It will flag any persistent heat source. In the Permian Basin and Eagle
Ford — sparse desert/scrubland with little wildfire activity and dense
well clusters — a detection that recurs at the same fixed point night
after night is almost certainly a flare, not a fire, but this script
doesn't prove that; see README.

Requires a free MAP_KEY (https://firms.modaps.eosdis.nasa.gov/api/map_key/)
in a local .env file as FIRMS_MAP_KEY=... (never commit this file).
"""

import os
import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_data import texas_polygon  # noqa: E402

load_dotenv()

MAP_KEY = os.environ.get("FIRMS_MAP_KEY")
SOURCES = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
DAY_RANGE = 5  # max allowed per request for these sources
TEXAS_BBOX = "-106.65,25.84,-93.51,36.50"  # cheap pre-filter before exact polygon test

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"


def fetch_source(source: str) -> pd.DataFrame:
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{source}/{TEXAS_BBOX}/{DAY_RANGE}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    if resp.text.startswith("Invalid") or resp.text.startswith("Error"):
        raise RuntimeError(f"{source}: {resp.text.strip()}")
    df = pd.read_csv(StringIO(resp.text))
    df["source"] = source
    return df


def main() -> None:
    if not MAP_KEY:
        raise SystemExit(
            "FIRMS_MAP_KEY not set. Get a free key at "
            "https://firms.modaps.eosdis.nasa.gov/api/map_key/ and put it in "
            "a local .env file as FIRMS_MAP_KEY=... (not committed to git)."
        )

    print(f"Fetching last {DAY_RANGE} days of VIIRS detections from {len(SOURCES)} satellites...")
    frames = [fetch_source(s) for s in SOURCES]
    combined = pd.concat(frames, ignore_index=True)
    print(f"  {len(combined):,} raw detections in the Texas bounding box, all satellites combined")

    night = combined[combined["daynight"] == "N"].copy()
    print(f"  {len(night):,} are nighttime detections (the cleaner flare signal)")

    tx_poly = texas_polygon()
    from shapely.geometry import Point
    in_tx = night.apply(lambda r: tx_poly.contains(Point(r["longitude"], r["latitude"])), axis=1)
    tx_night = night[in_tx].reset_index(drop=True)
    print(f"  {len(tx_night):,} are inside the actual Texas polygon (not just the bounding box)")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "tx_firms_current.csv"
    tx_night.to_csv(out_path, index=False)
    date_range = f"{tx_night['acq_date'].min()} to {tx_night['acq_date'].max()}" if len(tx_night) else "no data"
    print(f"\nSaved {len(tx_night):,} current Texas nighttime detections ({date_range}) to {out_path}")


if __name__ == "__main__":
    main()
