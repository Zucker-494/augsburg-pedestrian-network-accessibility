"""Generate a compact Markdown result summary after Project03 completes."""

from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "outputs"
PROC = BASE / "data" / "processed"

summary = pd.read_csv(
    OUT / "summary_metrics.csv"
)
build = pd.read_csv(
    PROC / "network_build_summary.csv"
)
snap = pd.read_csv(
    OUT / "store_snapping.csv"
)

metric = dict(
    zip(summary["metric"], summary["value"])
)
build_metric = dict(
    zip(build["metric"], build["value"])
)

max_snap_row = snap.loc[
    snap["snap_distance_m"].idxmax()
]

text = f"""# Project03 Results Summary

This file is generated automatically by the reproducible Project03 pipeline.

## Study area and network

- Augsburg municipal area: **{build_metric.get('municipal_boundary_area_km2', float('nan')):.2f} km²**
- Raw routable network nodes: **{build_metric.get('network_nodes', float('nan')):,.0f}**
- Raw routable network edges: **{build_metric.get('network_edges', float('nan')):,.0f}**
- Total represented edge length: **{build_metric.get('total_edge_length_km', float('nan')):,.1f} km**
- Connected components: **{metric.get('graph_components', float('nan')):,.0f}**
- Largest-component share: **{metric.get('largest_component_share_pct', float('nan')):.2f}%**

## Accessibility

- Analysed graph nodes: **{metric.get('graph_nodes_analysed', float('nan')):,.0f}**
- Median Euclidean distance: **{metric.get('median_euclidean_distance_m', float('nan'))/1000:.2f} km**
- Median pedestrian-network distance: **{metric.get('median_network_distance_m', float('nan'))/1000:.2f} km**
- P90 pedestrian-network distance: **{metric.get('p90_network_distance_m', float('nan'))/1000:.2f} km**
- Median detour ratio: **{metric.get('median_detour_ratio', float('nan')):.2f}**
- P90 detour ratio: **{metric.get('p90_detour_ratio', float('nan')):.2f}**
- Network nodes within 10 min: **{metric.get('share_nodes_within_10min_pct', float('nan')):.1f}%**
- Network nodes within 15 min: **{metric.get('share_nodes_within_15min_pct', float('nan')):.1f}%**

## Snapping QA

Maximum supermarket-to-network snap distance:

**{max_snap_row['snap_distance_m']:.1f} m — {max_snap_row['name']}**

The network-distance calculation includes this store-to-network connector, so
the comparison is made from the actual supermarket point rather than treating
the snapped network node as the supermarket itself.

## Interpretation boundary

These results refer to the current sampled supermarkets and the OSM pedestrian-network representation.

Walking time is derived from network distance using a fixed reference speed of
4.8 km/h. It is a comparative accessibility indicator, not an observed
pedestrian travel-time model.
"""

(OUT / "RESULTS_SUMMARY.md").write_text(
    text,
    encoding="utf-8",
)
print(text)
