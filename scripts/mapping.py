"""Shared basemap plotting for the two detection maps (historical and
current). Uses Esri's free tile service via contextily — tested against
three "free" alternatives first: CartoDB now requires an API key,
OpenStreetMap's own Mapnik tiles actively reject library/script access
per their usage policy (not a bug — see osm.wiki/Blocked), and Esri's
World Topo tiles are the one that's actually open for this kind of use.
"""

from pathlib import Path

import contextily as cx
import matplotlib.pyplot as plt

TEXAS_XLIM = (-107, -93)
TEXAS_YLIM = (25.5, 37)


def plot_texas_detections(
    lon, lat, title: str, out_path: Path, color: str = "red",
    s: float = 12, alpha: float = 0.75, edgecolors: str = "black",
) -> None:
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.scatter(lon, lat, s=s, alpha=alpha, color=color, zorder=5, edgecolors=edgecolors, linewidths=0.2)
    ax.set_xlim(*TEXAS_XLIM)
    ax.set_ylim(*TEXAS_YLIM)
    ax.set_title(title)
    ax.set_axis_off()
    cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.Esri.WorldTopoMap)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
