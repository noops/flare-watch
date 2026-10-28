# Flare Watch

Where Texas oil & gas flaring happens, who's nearest to it, and how it's
trended — built on public satellite data, no registration required.

Status: **v0 — real analysis on real (if dated) data.** Part of
[Bat City AI](https://batcityai.com)'s Year One programs.

## What it does

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/fetch_data.py   # ~1 min: downloads + Texas-filters the data
python3 scripts/analyze.py      # ~30s: map, trend, operator leaderboard
```

Produces:
- **A map** of every satellite-detected flare in Texas — the Permian
  Basin and Eagle Ford light up exactly where you'd expect.
- **A monthly trend** of detections vs. state-reported flaring volume.
  The 2020 oil crash is visible in both series.
- **A "top operators" leaderboard** — each detection matched to its
  nearest Texas well (within 2km) via a spatial join, then counted up by
  operator.

## The honest caveat that matters most

**This data runs from January 2019 to May 2021 — it is not current.**
The dataset this project builds on (see Data Sources) stopped being
updated at some point; it is not a live feed. "Flare Watch" is
aspirational for now. This v0 proves the pipeline and the Texas-specific
analysis work correctly on real satellite data; getting current data
is the clear next step (see Known Limitations).

Within that window, the data checks out against reality: both satellite
detections and state-reported volumes crater in exactly the months
Texas drilling activity actually crashed (the COVID demand shock +
2020 oil price war).

## Why a real polygon, not a bounding box

Texas and New Mexico share a border that runs straight through the
Permian Basin — exactly where most of this flaring happens. A naive
lat/lon bounding box around Texas would scoop up New Mexico detections.
`fetch_data.py` uses Texas's actual boundary polygon (from the same
dataset) for an exact point-in-polygon filter instead: of ~501,000
detections in the Texas bounding box, **71,000 (14%) were actually
across the border in New Mexico** and get correctly excluded.

## The operator leaderboard isn't a legal claim

"Nearest well within 2km" is a reasonable first-pass attribution, not
proof a specific well caused a specific flare. Flares can be offset from
the wellhead, wells cluster tightly together, and satellite geolocation
has its own error. 92% of detections matched a well within 2km; the
other 8% are excluded from the leaderboard rather than guessed at.

## Prior art

[FlareIntel](https://flareintel.com) (by Capterio) is a global, more
polished, more current flare tracker built on the same VIIRS/Nightfire
data, with operator and field attribution already built in — worth
knowing about before assuming this space is empty. As far as public
documentation shows, FlareIntel Free gives annualized aggregates through
an interactive map, with daily/near-real-time data reserved for the paid
Pro tier, and no confirmed bulk CSV export or API for either. This
project is narrower (Texas only) but open end to end: every raw input
file, the exact spatial-join logic, and the full attributed-detection
output are all re-runnable and inspectable, not a hosted black box.
Worth revisiting this comparison once v1 has current data — a head-to-head
against FlareIntel's numbers would be a good sanity check either way.

## Data sources

- **Satellite detections**: NOAA/NASA VIIRS Nightfire (radiant heat +
  location of combustion sources at night), via
  [flaringmonitor/viirs-flare-data](https://github.com/flaringmonitor/viirs-flare-data) —
  a public mirror that requires no signup. The official source
  ([eogdata.mines.edu](https://eogdata.mines.edu/products/vnf/)) has more
  current data but requires a free account; worth pursuing for v1.
- **Well locations & operators**: same mirror, sourced from Texas
  Railroad Commission well records.
- **State-reported flaring volumes**: same mirror, sourced from Texas
  Railroad Commission reporting.

## Known limitations (v1 candidates)

- **Not current.** The single biggest gap. Registering for a free EOG
  account would unlock current VIIRS Nightfire data; re-running this
  pipeline against that feed (same Texas-polygon filter, same spatial
  join) is the natural v1.
- **2km match radius wasn't tuned.** Chosen as a reasonable-sounding
  default, not validated against ground truth.
- **Detection counts, not flare volumes.** The operator leaderboard
  counts satellite detections, which isn't the same as total gas flared
  — a well flaring continuously for a month and one flaring for a single
  night could show up very differently depending on satellite pass
  timing. `rh` (radiant heat) is in the data and unused — summing it
  per operator would be a more physically meaningful metric than a raw
  count.
- **No temporal pattern analysis.** Do specific operators flare more at
  night, on weekends, or right before reporting deadlines? The data
  (timestamps + state-reported monthly totals) could answer this; it
  hasn't been asked yet.

## License

MIT
