# Project03 Status

## Implemented

- Augsburg municipal boundary fixed to OSM relation 62407 (`admin_level=6`)
- rectangle-based final clipping removed
- exact segment–polygon intersection implemented
- Augsburg-specific Overpass network acquisition implemented
- low-memory OSM XML parsing implemented
- pedestrian routing filters implemented
- `area=yes` highway polygons excluded from graph routing
- metric graph construction in EPSG:32632 implemented
- OSM pedestrian attributes retained
- network-attribute completeness diagnostics implemented
- connected-component diagnostics implemented
- largest-component routing implemented
- supermarket-to-network snapping implemented
- supermarket snap distance included in network cost
- multi-source Dijkstra accessibility implemented
- Euclidean/network comparison implemented
- detour ratio implemented
- walking-time accessibility implemented
- static figures implemented
- walking-accessibility Figure 3 revised to an ECDF with explicit 10/15-minute graph-node shares
- interactive OSM map implemented
- GeoPackage GIS working outputs implemented
- GitHub Actions cloud workflow implemented

## Pending before final freeze

Run the workflow against the live Augsburg network and inspect:

1. total node/edge counts;
2. largest-component share;
3. supermarket snap distances;
4. detour-ratio distribution and any ratios below 1;
5. visual quality of the static figures and interactive map.

The project should be frozen only after these checks pass.
