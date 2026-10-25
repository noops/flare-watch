# Flare Watch

Detects and tracks methane flaring events using public satellite data.

Status: idea. Part of [Bat City AI](https://batcityai.com)'s Year One programs.

## Plan

- **Data**: NOAA VIIRS Nightfire (existing flare-detection product — radiant heat +
  location, no image processing required for v0), cross-referenced against
  Texas Railroad Commission flare-permit data. Climate TRACE and Sentinel-5P /
  TROPOMI are longer-term options if the project moves toward raw detection.
- **Stack**: Python, satellite/geospatial data APIs
- **Goal v0**: map permitted vs. detected flares in Texas from VIIRS Nightfire data

## Status

Nothing shipped yet. See [Issues](../../issues) for current plan.

## License

MIT
