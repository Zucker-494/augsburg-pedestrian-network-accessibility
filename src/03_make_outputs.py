"""Create Project03 figures and an interactive OSM-based map."""

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import folium
import branca.colormap as bcm
from pyproj import Transformer

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"
OUT = BASE / "outputs"
DOCS = BASE / "docs"
OUT.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)


def main():
    nodes = gpd.read_file(PROC / "node_accessibility.gpkg", layer="accessibility")
    edges = gpd.read_file(PROC / "network_edges.gpkg", layer="edges")
    boundary = gpd.read_file(PROC / "augsburg_municipal_boundary.gpkg", layer="boundary")
    stores = pd.read_csv(BASE / "data" / "supermarkets_sample.csv")
    snapping = pd.read_csv(OUT / "store_snapping.csv")

    # Figure 1: Euclidean vs network distance
    sample = nodes.dropna(subset=["detour_ratio"]).sample(
        n=min(8000, len(nodes)),
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
    ax.plot([0, lim], [0, lim], linestyle="--", label="1:1 reference")
    ax.set_xlabel("Euclidean distance to nearest sampled supermarket (km)")
    ax.set_ylabel("Pedestrian-network distance (km)")
    ax.set_title("Euclidean vs Pedestrian-Network Accessibility")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "figure01_network_vs_euclidean.png", dpi=220)
    plt.close(fig)

    # Figure 2: detour ratio
    ratios = nodes["detour_ratio"].dropna()
    ratios = ratios[(ratios > 0) & (ratios < ratios.quantile(0.995))]
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.hist(ratios, bins=35)
    ax.axvline(ratios.median(), linestyle="--", label=f"Median = {ratios.median():.2f}")
    ax.set_xlabel("Detour ratio (network / Euclidean)")
    ax.set_ylabel("Network-node count")
    ax.set_title("Distribution of Pedestrian-Network Detour")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "figure02_detour_ratio_distribution.png", dpi=220)
    plt.close(fig)

    # Figure 3: walking-time distribution
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.hist(nodes["walking_time_min"], bins=35)
    ax.axvline(10, linestyle="--", label="10 min")
    ax.axvline(15, linestyle=":", label="15 min")
    ax.set_xlabel("Estimated walking time to nearest sampled supermarket (min)")
    ax.set_ylabel("Network-node count")
    ax.set_title("Network-Based Walking Accessibility")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "figure03_walking_accessibility.png", dpi=220)
    plt.close(fig)

    # Interactive map
    wgs_nodes = nodes.to_crs("EPSG:4326")
    wgs_edges = edges.to_crs("EPSG:4326")
    wgs_boundary = boundary.to_crs("EPSG:4326")

    m = folium.Map(
        location=[stores["latitude"].mean(), stores["longitude"].mean()],
        zoom_start=13,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # Municipal study boundary
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

    # Sample network edges for a clean default visual.
    if len(wgs_edges) > 12000:
        edge_display = wgs_edges.sample(12000, random_state=42)
    else:
        edge_display = wgs_edges

    network_group = folium.FeatureGroup(name="Pedestrian network", show=True)
    for geom in edge_display.geometry:
        coords = [(lat, lon) for lon, lat in geom.coords]
        folium.PolyLine(coords, weight=1, opacity=0.35).add_to(network_group)
    network_group.add_to(m)

    # High-detour nodes: top 10%
    valid = wgs_nodes.dropna(subset=["detour_ratio"]).copy()
    threshold = valid["detour_ratio"].quantile(0.90)
    hotspots = valid[valid["detour_ratio"] >= threshold].copy()
    if len(hotspots) > 1200:
        hotspots = hotspots.sample(1200, random_state=42)

    colormap = bcm.linear.YlOrRd_09.scale(
        float(hotspots["detour_ratio"].min()),
        float(hotspots["detour_ratio"].max()),
    )
    colormap.caption = "Detour ratio for top-10% network nodes"
    colormap.add_to(m)

    hotspot_group = folium.FeatureGroup(name="High-detour nodes", show=True)
    for row in hotspots.itertuples():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=3,
            weight=0,
            fill=True,
            fill_opacity=0.65,
            fill_color=colormap(row.detour_ratio),
            tooltip=(
                f"Detour ratio: {row.detour_ratio:.2f}<br>"
                f"Network: {row.network_distance_m/1000:.2f} km<br>"
                f"Euclidean: {row.euclidean_distance_m/1000:.2f} km"
            ),
        ).add_to(hotspot_group)
    hotspot_group.add_to(m)

    store_group = folium.FeatureGroup(name="Sample supermarkets", show=True)
    for _, r in stores.iterrows():
        folium.Marker(
            [r["latitude"], r["longitude"]],
            tooltip=r["name"],
            popup=f"<b>{r['name']}</b><br>{r['brand']}",
        ).add_to(store_group)
    store_group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    minx, miny, maxx, maxy = wgs_boundary.total_bounds
    m.fit_bounds([
        [miny, minx],
        [maxy, maxx],
    ])

    html = OUT / "interactive_network_accessibility.html"
    m.save(html)
    (DOCS / "index.html").write_text(html.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"Created {html}")


if __name__ == "__main__":
    main()
