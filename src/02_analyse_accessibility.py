"""Calculate supermarket accessibility on the Augsburg pedestrian graph.

The network cost includes the short connector from each supermarket point to
its snapped pedestrian-network node. This keeps the network-distance comparison
consistent with Euclidean distance measured from the actual supermarket point.
"""

from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import Point

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

    if G.number_of_nodes() == 0:
        raise RuntimeError("The pedestrian graph is empty.")

    # Connectivity QA
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    largest_nodes = components[0]
    largest_pct = len(largest_nodes) / G.number_of_nodes() * 100.0

    component_summary = pd.DataFrame(
        {
            "component_rank": np.arange(1, len(components) + 1),
            "node_count": [len(c) for c in components],
        }
    )
    component_summary["share_of_all_nodes_pct"] = (
        component_summary["node_count"] / G.number_of_nodes() * 100.0
    )
    component_summary.to_csv(OUT / "network_component_summary.csv", index=False)

    G = G.subgraph(largest_nodes).copy()

    # Save only the routing component used for maps and analysis.
    lcc_ids = set(int(n) for n in G.nodes())
    edges_lcc = edges[
        edges["u"].astype(int).isin(lcc_ids)
        & edges["v"].astype(int).isin(lcc_ids)
    ].copy()
    edges_lcc.to_file(
        PROC / "network_edges_lcc.gpkg",
        layer="edges",
        driver="GPKG",
    )

    node_ids = np.array(list(G.nodes()), dtype=int)
    node_xy = np.array(
        [[G.nodes[n]["x"], G.nodes[n]["y"]] for n in node_ids],
        dtype=float,
    )
    tree = cKDTree(node_xy)

    # Project supermarket point coordinates into UTM 32N.
    to_utm = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:32632",
        always_xy=True,
    )
    store_x, store_y = to_utm.transform(
        stores["longitude"].to_numpy(),
        stores["latitude"].to_numpy(),
    )
    store_xy = np.column_stack([store_x, store_y])

    # Snap stores to the largest connected pedestrian component.
    snap_d, snap_idx = tree.query(store_xy)
    store_nodes = node_ids[snap_idx]

    snapping = stores[
        ["name", "brand", "latitude", "longitude"]
    ].copy()
    snapping["graph_node"] = store_nodes
    snapping["snap_distance_m"] = snap_d
    snapping.to_csv(OUT / "store_snapping.csv", index=False)

    # ------------------------------------------------------------------
    # IMPORTANT:
    # Represent each supermarket as a virtual graph source connected to
    # the snapped street node by its snap distance.
    #
    # This means network distance is measured from the actual store point,
    # not artificially from the snapped node.
    # ------------------------------------------------------------------
    H = G.copy()
    virtual_sources = []
    source_to_store = {}

    for i, row in snapping.iterrows():
        virtual = f"store::{i}"
        graph_node = int(row["graph_node"])
        snap_cost = float(row["snap_distance_m"])

        H.add_node(virtual, virtual_store=True)
        H.add_edge(
            virtual,
            graph_node,
            length_m=snap_cost,
        )
        virtual_sources.append(virtual)
        source_to_store[virtual] = row["name"]

    distances, paths = nx.multi_source_dijkstra(
        H,
        sources=virtual_sources,
        weight="length_m",
    )

    # Euclidean comparator is still measured to the actual store coordinates.
    store_tree = cKDTree(store_xy)

    records = []
    for node_id in node_ids:
        node_id = int(node_id)
        if node_id not in distances:
            continue

        x = float(G.nodes[node_id]["x"])
        y = float(G.nodes[node_id]["y"])

        euclid_m, nearest_store_idx = store_tree.query([x, y])
        network_m = float(distances[node_id])
        path = paths[node_id]

        virtual_source = path[0]
        nearest_network_store = source_to_store.get(
            virtual_source,
            "Unknown",
        )

        # Avoid unstable ratios extremely close to a supermarket.
        ratio = np.nan
        if float(euclid_m) >= 50:
            ratio = network_m / float(euclid_m)

        records.append(
            {
                "node_id": node_id,
                "x": x,
                "y": y,
                "euclidean_distance_m": float(euclid_m),
                "network_distance_m": network_m,
                "walking_time_min": network_m / WALKING_SPEED_M_PER_MIN,
                "detour_ratio": ratio,
                "nearest_euclidean_store": stores.iloc[
                    int(nearest_store_idx)
                ]["name"],
                "nearest_network_store": nearest_network_store,
            }
        )

    metrics = pd.DataFrame(records)

    if metrics.empty:
        raise RuntimeError(
            "No accessibility records were produced."
        )

    accessibility = gpd.GeoDataFrame(
        metrics,
        geometry=[
            Point(xy)
            for xy in zip(metrics["x"], metrics["y"])
        ],
        crs="EPSG:32632",
    )
    accessibility.to_file(
        PROC / "node_accessibility.gpkg",
        layer="accessibility",
        driver="GPKG",
    )

    valid_ratio = metrics["detour_ratio"].dropna()

    # Numerical/topological QA: detour should not materially fall below 1
    # after the store-to-network connector is included.
    below_one = int((valid_ratio < 0.995).sum())

    summary = pd.DataFrame(
        {
            "metric": [
                "graph_components",
                "largest_component_nodes",
                "largest_component_share_pct",
                "graph_nodes_analysed",
                "median_euclidean_distance_m",
                "median_network_distance_m",
                "p90_network_distance_m",
                "median_detour_ratio",
                "p90_detour_ratio",
                "share_nodes_within_10min_pct",
                "share_nodes_within_15min_pct",
                "max_store_snap_distance_m",
                "detour_ratio_below_0_995_count",
            ],
            "value": [
                len(components),
                len(largest_nodes),
                largest_pct,
                len(metrics),
                metrics["euclidean_distance_m"].median(),
                metrics["network_distance_m"].median(),
                metrics["network_distance_m"].quantile(0.90),
                valid_ratio.median(),
                valid_ratio.quantile(0.90),
                (metrics["walking_time_min"] <= 10).mean() * 100,
                (metrics["walking_time_min"] <= 15).mean() * 100,
                snapping["snap_distance_m"].max(),
                below_one,
            ],
        }
    )

    summary.to_csv(
        OUT / "summary_metrics.csv",
        index=False,
    )

    print("\nConnectivity diagnostics")
    print(
        f"Components: {len(components):,}; "
        f"largest component: {len(largest_nodes):,} nodes "
        f"({largest_pct:.2f}%)."
    )

    print("\nStore snapping")
    print(
        snapping[
            ["name", "graph_node", "snap_distance_m"]
        ].to_string(index=False)
    )

    print("\nAccessibility summary")
    print(summary.to_string(index=False))

    if below_one:
        print(
            "\nWARNING: Some detour ratios are slightly below 1. "
            "Inspect floating-point/topological effects before interpretation."
        )


if __name__ == "__main__":
    main()
