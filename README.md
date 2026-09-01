# Project03 — Pedestrian Network Accessibility in Augsburg

## Project objective

Project03 extends the Euclidean accessibility work from Project02 into a **real street-network model**.

The core question is:

> How different is supermarket accessibility when actual pedestrian-network structure is considered instead of straight-line distance?

The project is designed as an intermediate GIS/network-analysis portfolio case. It demonstrates how the choice of spatial representation changes accessibility results.

---

## Planned analytical workflow

```text
Augsburg-specific Overpass OSM XML
            │
            ▼
Extract Augsburg municipal boundary
            │
            ▼
Clip highways to the municipal polygon
            │
            ▼
Filter pedestrian-usable links
            │
            ▼
Segment lines into a topological graph
            │
            ▼
Snap supermarket POIs to graph nodes
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
              Spatial diagnostics + maps
```

The main comparison is:

\[
Detour\ Ratio = rac{Network\ Distance}{Euclidean\ Distance}
\]

A detour ratio close to 1 means the pedestrian network provides a relatively direct route. Higher values indicate that barriers, street configuration or limited crossings create additional travel distance.

---

## Expected outputs

After the OSM extract is added and the pipeline is run, the project will generate:

- `network_nodes.gpkg`
- `network_edges.gpkg`
- `node_accessibility.gpkg`
- `store_snapping.csv`
- `summary_metrics.csv`
- `figure01_network_vs_euclidean.png`
- `figure02_detour_ratio_distribution.png`
- `figure03_walking_accessibility.png`
- `interactive_network_accessibility.html`

The interactive output uses an OpenStreetMap basemap.

---

## Data required

Use the two Augsburg-specific Overpass exports and save them as:

```text
data/raw/schwaben-latest.osm.pbf
```

The file covers Augsburg and is roughly 121 MB.

No network result is fabricated if the file is absent.

See `DATA_DOWNLOAD.md`.

---

## Study data

The supermarket sample is inherited from Project02 so that the methodological comparison remains controlled.

This means the main change between Project02 and Project03 is the **distance representation**:

- Project02: Euclidean distance
- Project03: pedestrian-network distance

This is useful because differences can be interpreted as network effects rather than changes in the retail sample.

---

## Reproducibility

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python src/run_project03.py
```

The pipeline will stop with a clear message if the OSM PBF is missing.

---

## Portfolio skills demonstrated

Once completed, Project03 demonstrates:

- direct OpenStreetMap PBF processing;
- administrative-boundary extraction and polygon clipping;
- pedestrian-network extraction;
- graph construction with NetworkX;
- spatial snapping using nearest-neighbour search;
- multi-source shortest-path analysis;
- Euclidean versus network accessibility;
- detour-ratio diagnostics;
- walking-time modelling;
- GeoParquet-based intermediate data;
- interactive web cartography.

---

## Methodological boundary

This is a network accessibility model, not a complete pedestrian-behaviour model.

The graph represents OSM-mapped walkable street structure. It does not model individual mobility constraints, signal waiting time, crossing difficulty, slope, crowding or temporary barriers.

Walking time is estimated from network distance using a fixed reference walking speed and is therefore a comparative indicator.


---

## Study-area definition

The analytical study area is the **Augsburg municipal administrative boundary**, not a rectangular analysis extent.

The pipeline extracts the Augsburg administrative relation from the same Geofabrik OSM PBF, saves it as `augsburg_municipal_boundary.geojson`, and clips the pedestrian network to that polygon.

A rectangular bounding box may still be used internally to reduce PBF read time. It is only an I/O optimisation and does not define the analytical study area.


---

## Current data architecture

The final Project03 pipeline uses the smaller Augsburg-specific exports rather
than requiring users to download the full Schwaben extract:

```text
data/raw/augsburg_boundary.geojson
data/raw/augsburg_pedestrian_network.osm
```

The boundary is OSM relation **62407**, `admin_level=6`.

The network export contains detailed pedestrian attributes in parts of Augsburg,
including `surface`, `smoothness`, `incline`, `steps`, lighting and crossing
information. Project03 measures the completeness of these attributes but keeps
the baseline routing cost equal to physical network distance. This avoids
introducing undocumented subjective penalty weights.


---

## One-click cloud reproduction

Project03 includes a **GitHub Actions** workflow, so the network model does not
need to be computed on a powerful local computer.

After uploading the repository:

**Actions → Build Project03 GIS Analysis → Run workflow**

The cloud runner downloads the public Augsburg OSM inputs, builds the graph,
runs Dijkstra accessibility analysis, generates all maps/results, and commits
the portfolio outputs back to the repository.

See [`CLOUD_BUILD.md`](CLOUD_BUILD.md).

This automation is part of the portfolio value of Project03: the project
demonstrates both network GIS analysis and a reproducible computational workflow.
