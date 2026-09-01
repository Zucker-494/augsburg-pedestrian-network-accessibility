"""Generate a compact Markdown summary after Project03 completes."""

from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "outputs"

summary = pd.read_csv(OUT / "summary_metrics.csv")
build = pd.read_csv(BASE / "data" / "processed" / "network_build_summary.csv")
snap = pd.read_csv(OUT / "store_snapping.csv")

metric = dict(zip(summary["metric"], summary["value"]))
build_metric = dict(zip(build["metric"], build["value"]))

max_snap_row = snap.loc[snap["snap_distance_m"].idxmax()]

text = f"""# Project03 Results Summary

This file is generated automatically by the reproducible Project03 pipeline.

## Network

- Augsburg municipal area: **{build_metric.get('municipal_boundary_area_km2', float('nan')):.2f} km²**
- Routable network nodes: **{build_metric.get('network_nodes', float('nan')):,.0f}**
- Routable network edges: **{build_metric.get('network_edges', float('nan')):,.0f}**
- Total represented edge length: **{build_metric.get('total_edge_length_km', float('nan')):,.1f} km**

## Accessibility

- Median Euclidean distance: **{metric.get('median_euclidean_distance_m', float('nan'))/1000:.2f} km**
- Median pedestrian-network distance: **{metric.get('median_network_distance_m', float('nan'))/1000:.2f} km**
- P90 pedestrian-network distance: **{metric.get('p90_network_distance_m', float('nan'))/1000:.2f} km**
- Median detour ratio: **{metric.get('median_detour_ratio', float('nan')):.2f}**
- P90 detour ratio: **{metric.get('p90_detour_ratio', float('nan')):.2f}**
- Network nodes within 10 min: **{metric.get('share_nodes_within_10min_pct', float('nan')):.1f}%**
- Network nodes within 15 min: **{metric.get('share_nodes_within_15min_pct', float('nan')):.1f}%**

## Snapping QA

Maximum supermarket-to-network-node snap distance:

**{max_snap_row['snap_distance_m']:.1f} m — {max_snap_row['name']}**

Large snap distances should be inspected before interpreting the model.

## Interpretation boundary

These results refer to the current sampled supermarkets and OSM pedestrian-network representation.

Walking time is derived from network distance using a fixed reference speed; it is not an observed pedestrian travel-time model.
"""

(OUT / "RESULTS_SUMMARY.md").write_text(text, encoding="utf-8")
print(text)
