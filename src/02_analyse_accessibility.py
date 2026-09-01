"""Calculate supermarket accessibility on the pedestrian graph."""

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from scipy.spatial import cKDTree
from shapely.geometry import Point
from pyproj import Transformer

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"
OUT = BASE / "outputs"
OUT.mkdir(exist_ok=True)

WALKING_SPEED_M_PER_MIN = 80.0  # 4.8 km/h reference speed


def main():
    nodes = gpd.read_file(PROC / "network_nodes.gpkg", layer="nodes")
    edges = gpd.read_file(PROC / "network_edges.gpkg", layer="edges")
    stores = pd.read_csv(BASE / "data" / "supermarkets_sample.csv")

    G = nx.Graph()

    for row in nodes.itertuples():
        G.add_node(int(row.node_id), x=float(row.x), y=float(row.y))

    for row in edges.itertuples():
        u, v, w = int(row.u), int(row.v), float(row.length_m)
        # Preserve the shortest segment if duplicate graph edges occur.
        if G.has_edge(u, v):
            if w < G[u][v]["length_m"]:
                G[u][v]["length_m"] = w
        else:
            G.add_edge(u, v, length_m=w)

    # Work on largest connected component to prevent disconnected fringe artifacts.
    components = list(nx.connected_components(G))
    largest_nodes = max(components, key=len)
    G = G.subgraph(largest_nodes).copy()

    node_ids = np.array(list(G.nodes()), dtype=int)
    node_xy = np.array([[G.nodes[n]["x"], G.nodes[n]["y"]] for n in node_ids])
    tree = cKDTree(node_xy)

    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32632", always_xy=True)
    store_x, store_y = to_utm.transform(
        stores["longitude"].to_numpy(),
        stores["latitude"].to_numpy(),
    )
    store_xy = np.column_stack([store_x, store_y])

    snap_d, snap_idx = tree.query(store_xy)
    store_nodes = node_ids[snap_idx]

    snapping = stores[["name", "brand", "latitude", "longitude"]].copy()
    snapping["graph_node"] = store_nodes
    snapping["snap_distance_m"] = snap_d
    snapping.to_csv(OUT / "store_snapping.csv", index=False)

    # Remove duplicate sources if two stores snap to the same graph node.
    unique_source_nodes = list(dict.fromkeys(int(n) for n in store_nodes))

    distances, paths = nx.multi_source_dijkstra(
        G,
        sources=unique_source_nodes,
        weight="length_m",
    )

    # Map each snapped source graph node back to one representative store.
    source_to_store = {}
    for i, n in enumerate(store_nodes):
        source_to_store.setdefault(int(n), stores.iloc[i]["name"])

    store_tree = cKDTree(store_xy)

    records = []
    for node_id in node_ids:
        if int(node_id) not in distances:
            continue

        x = G.nodes[int(node_id)]["x"]
        y = G.nodes[int(node_id)]["y"]

        euclid_m, nearest_store_idx = store_tree.query([x, y])
        network_m = float(distances[int(node_id)])
        path = paths[int(node_id)]
        source_node = int(path[0])
        nearest_network_store = source_to_store.get(source_node, "Unknown")

        ratio = np.nan
        if euclid_m >= 50:
            ratio = network_m / float(euclid_m)

        records.append(
            {
                "node_id": int(node_id),
                "x": x,
                "y": y,
                "euclidean_distance_m": float(euclid_m),
                "network_distance_m": network_m,
                "walking_time_min": network_m / WALKING_SPEED_M_PER_MIN,
                "detour_ratio": ratio,
                "nearest_euclidean_store": stores.iloc[int(nearest_store_idx)]["name"],
                "nearest_network_store": nearest_network_store,
            }
        )

    metrics = pd.DataFrame(records)
    gdf = gpd.GeoDataFrame(
        metrics,
        geometry=[Point(xy) for xy in zip(metrics["x"], metrics["y"])],
        crs="EPSG:32632",
    )
    gdf.to_file(PROC / "node_accessibility.gpkg", layer="accessibility", driver="GPKG")

    valid_ratio = metrics["detour_ratio"].dropna()
    summary = pd.DataFrame(
        {
            "metric": [
                "graph_nodes_analysed",
                "median_euclidean_distance_m",
                "median_network_distance_m",
                "p90_network_distance_m",
                "median_detour_ratio",
                "p90_detour_ratio",
                "share_nodes_within_10min_pct",
                "share_nodes_within_15min_pct",
                "max_store_snap_distance_m",
            ],
            "value": [
                len(metrics),
                metrics["euclidean_distance_m"].median(),
                metrics["network_distance_m"].median(),
                metrics["network_distance_m"].quantile(0.90),
                valid_ratio.median(),
                valid_ratio.quantile(0.90),
                (metrics["walking_time_min"] <= 10).mean() * 100,
                (metrics["walking_time_min"] <= 15).mean() * 100,
                snapping["snap_distance_m"].max(),
            ],
        }
    )
    summary.to_csv(OUT / "summary_metrics.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
