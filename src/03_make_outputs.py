"""Create Project03 figures and an interactive OSM-based map."""

from pathlib import Path

import branca.colormap as bcm
import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"
OUT = BASE / "outputs"
DOCS = BASE / "docs"

OUT.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)


def main():
    nodes = gpd.read_file(
        PROC / "node_accessibility.gpkg",
        layer="accessibility",
    )
    edges = gpd.read_file(
        PROC / "network_edges_lcc.gpkg",
        layer="edges",
    )
    boundary = gpd.read_file(
        PROC / "augsburg_municipal_boundary.gpkg",
        layer="boundary",
    )
    stores = pd.read_csv(
        BASE / "data" / "supermarkets_sample.csv"
    )

    # ---------------------------------------------------------------
    # Figure 1: Euclidean vs network distance
    # ---------------------------------------------------------------
    scatter_source = nodes.dropna(
        subset=[
            "euclidean_distance_m",
            "network_distance_m",
            "detour_ratio",
        ]
    ).copy()

    if scatter_source.empty:
        raise RuntimeError(
            "No valid nodes are available for accessibility figures."
        )

    sample = scatter_source.sample(
        n=min(8000, len(scatter_source)),
        random_state=42,
    )

    fig, ax = plt.subplots(figsize=(7.5, 6.2))
    ax.scatter(
        sample["euclidean_distance_m"] / 1000,
        sample["network_distance_m"] / 1000,
        s=8,
        alpha=0.35,
    )

    lim = max(
        sample["euclidean_distance_m"].max(),
        sample["network_distance_m"].max(),
    ) / 1000

    ax.plot(
        [0, lim],
        [0, lim],
        linestyle="--",
        label="1:1 reference",
    )
    ax.set_xlabel(
        "Euclidean distance to nearest sampled supermarket (km)"
    )
    ax.set_ylabel(
        "Pedestrian-network distance (km)"
    )
    ax.set_title(
        "Euclidean vs Pedestrian-Network Accessibility"
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        OUT / "figure01_network_vs_euclidean.png",
        dpi=220,
    )
    plt.close(fig)

    # ---------------------------------------------------------------
    # Figure 2: detour-ratio distribution
    # ---------------------------------------------------------------
    ratios = nodes["detour_ratio"].dropna()
    ratios = ratios[ratios > 0]

    if ratios.empty:
        raise RuntimeError(
            "No valid detour ratios were produced."
        )

    # Only trim the extreme 0.5% for visualization; summary metrics use
    # the full valid distribution.
    upper = ratios.quantile(0.995)
    ratios_plot = ratios[ratios <= upper]

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.hist(ratios_plot, bins=35)
    ax.axvline(
        ratios.median(),
        linestyle="--",
        label=f"Median = {ratios.median():.2f}",
    )
    ax.set_xlabel(
        "Detour ratio (network / Euclidean)"
    )
    ax.set_ylabel(
        "Network-node count"
    )
    ax.set_title(
        "Distribution of Pedestrian-Network Detour"
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        OUT / "figure02_detour_ratio_distribution.png",
        dpi=220,
    )
    plt.close(fig)

    # ---------------------------------------------------------------
    # Figure 3: walking-time distribution
    # ---------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.hist(
        nodes["walking_time_min"].dropna(),
        bins=35,
    )
    ax.axvline(10, linestyle="--", label="10 min")
    ax.axvline(15, linestyle=":", label="15 min")
    ax.set_xlabel(
        "Estimated walking time to nearest sampled supermarket (min)"
    )
    ax.set_ylabel(
        "Network-node count"
    )
    ax.set_title(
        "Network-Based Walking Accessibility"
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        OUT / "figure03_walking_accessibility.png",
        dpi=220,
    )
    plt.close(fig)

    # ---------------------------------------------------------------
    # Interactive map
    # ---------------------------------------------------------------
    wgs_nodes = nodes.to_crs("EPSG:4326")
    wgs_edges = edges.to_crs("EPSG:4326")
    wgs_boundary = boundary.to_crs("EPSG:4326")

    m = folium.Map(
        location=[
            stores["latitude"].mean(),
            stores["longitude"].mean(),
        ],
        zoom_start=13,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    boundary_group = folium.FeatureGroup(
        name="Augsburg municipal boundary",
        show=True,
    )
    folium.GeoJson(
        wgs_boundary.__geo_interface__,
        style_function=lambda feature: {
            "fillOpacity": 0.0,
            "weight": 3,
        },
        tooltip="Augsburg municipal boundary",
    ).add_to(boundary_group)
    boundary_group.add_to(m)

    # Sample edges only for browser performance.
    if len(wgs_edges) > 12000:
        edge_display = wgs_edges.sample(
            12000,
            random_state=42,
        )
    else:
        edge_display = wgs_edges

    network_group = folium.FeatureGroup(
        name="Pedestrian network",
        show=True,
    )
    for geom in edge_display.geometry:
        if geom is None or geom.is_empty:
            continue
        coords = [
            (lat, lon)
            for lon, lat in geom.coords
        ]
        folium.PolyLine(
            coords,
            weight=1,
            opacity=0.35,
        ).add_to(network_group)
    network_group.add_to(m)

    # High-detour nodes: top 10% of valid nodes.
    valid = wgs_nodes.dropna(
        subset=["detour_ratio"]
    ).copy()

    if not valid.empty:
        threshold = valid["detour_ratio"].quantile(0.90)
        hotspots = valid[
            valid["detour_ratio"] >= threshold
        ].copy()

        if len(hotspots) > 1200:
            hotspots = hotspots.sample(
                1200,
                random_state=42,
            )

        min_ratio = float(
            hotspots["detour_ratio"].min()
        )
        max_ratio = float(
            hotspots["detour_ratio"].max()
        )

        if max_ratio <= min_ratio:
            max_ratio = min_ratio + 0.01

        colormap = bcm.linear.YlOrRd_09.scale(
            min_ratio,
            max_ratio,
        )
        colormap.caption = (
            "Detour ratio for top-10% network nodes"
        )
        colormap.add_to(m)

        hotspot_group = folium.FeatureGroup(
            name="High-detour nodes",
            show=True,
        )

        for row in hotspots.itertuples():
            folium.CircleMarker(
                location=[
                    row.geometry.y,
                    row.geometry.x,
                ],
                radius=3,
                weight=0,
                fill=True,
                fill_opacity=0.65,
                fill_color=colormap(
                    row.detour_ratio
                ),
                tooltip=(
                    f"Detour ratio: {row.detour_ratio:.2f}<br>"
                    f"Network: {row.network_distance_m/1000:.2f} km<br>"
                    f"Euclidean: {row.euclidean_distance_m/1000:.2f} km"
                ),
            ).add_to(hotspot_group)

        hotspot_group.add_to(m)

    store_group = folium.FeatureGroup(
        name="Sample supermarkets",
        show=True,
    )

    for _, row in stores.iterrows():
        folium.Marker(
            [
                row["latitude"],
                row["longitude"],
            ],
            tooltip=row["name"],
            popup=(
                f"<b>{row['name']}</b><br>"
                f"{row['brand']}"
            ),
        ).add_to(store_group)

    store_group.add_to(m)

    folium.LayerControl(
        collapsed=False
    ).add_to(m)

    minx, miny, maxx, maxy = (
        wgs_boundary.total_bounds
    )
    m.fit_bounds(
        [
            [miny, minx],
            [maxy, maxx],
        ]
    )

    html = OUT / "interactive_network_accessibility.html"
    m.save(html)

    (DOCS / "index.html").write_text(
        html.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    print(f"Created {html}")


if __name__ == "__main__":
    main()
