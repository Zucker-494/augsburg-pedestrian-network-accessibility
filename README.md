# Project03 — Pedestrian Network Accessibility in Augsburg

## Project objective

Project03 extends the Euclidean accessibility analysis from Project02 into a
pedestrian street-network model.

The core question is:

> How different is supermarket accessibility when actual pedestrian-network
> structure is considered instead of straight-line distance?

The project keeps the supermarket sample consistent with Project02. The main
methodological change is therefore the representation of distance:

- **Project02:** Euclidean distance
- **Project03:** pedestrian-network distance

This makes the comparison interpretable as a network effect rather than a
change in the retail sample.

---

## Analytical workflow

```text
Augsburg municipal boundary
(OSM relation 62407, admin_level=6)
              │
              ▼
Augsburg-specific pedestrian OSM XML
              │
              ▼
Exact clip to the municipal polygon
              │
              ▼
Filter pedestrian-usable highway ways
              │
              ▼
Build topological graph in EPSG:32632
              │
              ▼
Largest-connected-component diagnostics
              │
              ▼
Snap supermarket points to the graph
              │
              ▼
Include store-to-network connector distance
              │
              ▼
Multi-source Dijkstra shortest paths
              │
              ├── Euclidean nearest-store distance
              ├── Network nearest-store distance
              ├── Walking-time accessibility
              └── Detour ratio
                           │
                           ▼
                Diagnostics + figures + map
```

The main diagnostic is:

```text
Detour ratio = pedestrian-network distance / Euclidean distance
```

A value near 1 indicates a relatively direct pedestrian-network route. Higher
values indicate additional travel distance created by street configuration,
barriers or limited connectivity.

---

## Study-area definition

The analytical study area is the **Augsburg municipal administrative boundary**,
not a rectangular extent.

The boundary is OpenStreetMap relation **62407**:

- `name=Augsburg`
- `boundary=administrative`
- `admin_level=6`

Each candidate OSM road segment is intersected with this polygon. Segments
crossing the municipal boundary are clipped at the real polygon boundary.

---

## Input data

The reproducible cloud workflow downloads two public OSM inputs automatically:

```text
data/raw/augsburg_boundary.geojson
data/raw/augsburg_pedestrian_network.osm
```

The pedestrian-network extract is obtained from Overpass for the Augsburg
administrative area. Obvious non-pedestrian road classes, `foot=no` and
`access=private` are excluded. A second validation step is performed in Python.

The supermarket comparison uses:

```text
data/supermarkets_sample.csv
```

This is the same eight-store sample used for the controlled comparison with
Project02.

See [`DATA_DOWNLOAD.md`](DATA_DOWNLOAD.md).

---

## Network model

OSM ways are converted into an undirected pedestrian graph. Segment lengths are
measured in **ETRS89 / UTM zone 32N (EPSG:32632)**.

The project reports connected-component structure before accessibility analysis.
Shortest-path analysis uses the largest connected component to reduce
disconnected fringe artifacts.

Each supermarket is snapped to its nearest node in the analysed component.
Importantly, the distance from the actual supermarket point to the snapped node
is included in network cost through a virtual store connector.

Walking time uses a fixed reference speed:

```text
80 m/min = 4.8 km/h
```

It is a comparative indicator rather than an observed travel-time model.

---

## OSM pedestrian attributes

The OSM network may contain attributes such as:

- `surface`
- `smoothness`
- `incline`
- `lit`
- `step_count`
- crossings, bridges and tunnels

Project03 reports attribute completeness but does **not** assign arbitrary
penalty weights to these fields. The baseline routing cost is physical network
distance.

This keeps the current model transparent while leaving a clear extension path
toward generalized-cost or accessibility-sensitive routing.

---

## Generated outputs

### Portfolio outputs

The cloud workflow generates and keeps:

```text
outputs/store_snapping.csv
outputs/network_component_summary.csv
outputs/summary_metrics.csv
outputs/RESULTS_SUMMARY.md
outputs/figure01_network_vs_euclidean.png
outputs/figure02_detour_ratio_distribution.png
outputs/figure03_walking_accessibility.png
outputs/interactive_network_accessibility.html
docs/index.html
```

`docs/index.html` is the GitHub Pages version of the interactive map.

### GIS working outputs

During execution, the pipeline also creates GeoPackage layers:

```text
data/processed/augsburg_municipal_boundary.gpkg
data/processed/network_nodes.gpkg
data/processed/network_edges.gpkg
data/processed/network_edges_lcc.gpkg
data/processed/node_accessibility.gpkg
```

These are available in the GitHub Actions artifact but are not committed to the
repository because they can be substantially larger than the portfolio figures
and tables.

---

## Reproducibility

### Cloud execution — recommended

No local GIS processing is required.

After the repository is on GitHub:

```text
Actions
→ Build Project03 GIS Analysis
→ Run workflow
```

GitHub Actions downloads the public OSM inputs and runs the complete pipeline.

See [`CLOUD_BUILD.md`](CLOUD_BUILD.md).

### Local execution

If a local run is desired:

```bash
pip install -r requirements.txt
python src/00_download_inputs.py
python src/run_project03.py
```

---

## Portfolio skills demonstrated

Project03 demonstrates:

- OpenStreetMap / Overpass data acquisition
- administrative-boundary polygon clipping
- pedestrian-network extraction
- graph construction with NetworkX
- connectivity diagnostics
- spatial nearest-neighbour snapping
- multi-source shortest-path analysis
- Euclidean versus network accessibility
- detour-ratio diagnostics
- walking-time modelling
- GeoPackage-based GIS outputs
- interactive web cartography
- GitHub Actions reproducible automation

---

## Methodological boundary

This is a **network accessibility model**, not a complete pedestrian-behaviour
model.

The graph represents OSM-mapped pedestrian street structure. It does not
directly model individual mobility constraints, signal waiting time, crossing
difficulty, crowding or temporary barriers. Network attribute completeness also
varies across OSM features.

Accordingly, results should be interpreted as spatial-network accessibility
diagnostics for the sampled supermarkets rather than observed pedestrian
behaviour.
