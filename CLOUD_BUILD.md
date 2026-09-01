# Cloud Build

Project03 is intended to be reproducible without running city-scale GIS analysis
on a local laptop.

## Run

On GitHub:

```text
Actions
→ Build Project03 GIS Analysis
→ Run workflow
→ Run workflow
```

The workflow then:

1. installs the Python/GIS environment;
2. downloads the Augsburg municipal boundary;
3. downloads the Augsburg pedestrian OSM network;
4. clips the network to the actual municipal polygon;
5. builds and diagnoses the graph;
6. snaps supermarket points to the graph;
7. runs multi-source Dijkstra;
8. calculates network distance, Euclidean distance, walking time and detour ratio;
9. creates static figures and an interactive map;
10. uploads the full GIS outputs as a GitHub Actions artifact;
11. commits the lighter portfolio outputs in `outputs/` and `docs/` back to `main`.

## Full GIS artifact

The workflow artifact includes `data/processed/` GeoPackages in addition to the
portfolio figures and tables. These larger GIS files are retained as an Actions
artifact rather than committed to the repository.

## GitHub Pages

After the workflow succeeds, `docs/index.html` contains the interactive map.

GitHub Pages can be enabled with:

```text
Settings
→ Pages
→ Deploy from a branch
→ main
→ /docs
```
