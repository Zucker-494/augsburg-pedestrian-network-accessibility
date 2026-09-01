# Cloud Build — No Local GIS Processing Required

Project03 includes a GitHub Actions workflow that runs the computationally
heavy steps on GitHub's cloud runner.

## Run the cloud build

After uploading the repository to GitHub:

1. Open the repository.
2. Click **Actions**.
3. Select **Build Project03 GIS Analysis**.
4. Click **Run workflow**.
5. Keep the branch as `main`.
6. Click the green **Run workflow** button.

GitHub automatically:

1. installs the GIS/Python dependencies;
2. downloads Augsburg relation 62407 as the municipal polygon;
3. downloads the pedestrian-network OSM XML from Overpass;
4. constructs the pedestrian graph;
5. snaps supermarket POIs to the graph;
6. runs multi-source Dijkstra shortest paths;
7. calculates Euclidean/network distance, walking time and detour ratio;
8. generates figures and the interactive map;
9. generates `outputs/RESULTS_SUMMARY.md`;
10. commits generated `outputs/` and `docs/` files back to the repository.

The large raw OSM files are removed before the automated commit.

## GitHub Pages

After the workflow succeeds, `docs/index.html` contains the interactive map.

Enable GitHub Pages using:

- branch: `main`
- folder: `/docs`

## Why this is useful

The cloud workflow uses the same source code stored in `src/`. It simply provides
a reproducible execution environment, so city-scale graph processing does not
depend on the user's laptop hardware.
