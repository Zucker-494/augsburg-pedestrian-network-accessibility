"""Build a pedestrian graph from the Augsburg Overpass exports.

Required external inputs
------------------------
data/raw/augsburg_boundary.geojson
data/raw/augsburg_pedestrian_network.osm

The network export is already restricted to Augsburg by the Overpass area
query. The municipal polygon is nevertheless applied again as the final,
explicit analytical clip.

OpenStreetMap data: © OpenStreetMap contributors, ODbL.
"""

from pathlib import Path
import json
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString, MultiLineString, Point, shape
from shapely.ops import transform as shapely_transform

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw"
PROC = BASE / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

BOUNDARY_FILE = RAW / "augsburg_boundary.geojson"
OSM_FILE = RAW / "augsburg_pedestrian_network.osm"

EXCLUDED_HIGHWAYS = {
    "motorway", "motorway_link", "trunk", "trunk_link",
    "raceway", "construction", "proposed",
}
EXCLUDED_ACCESS = {"private", "no"}


def load_boundary():
    if not BOUNDARY_FILE.exists():
        raise FileNotFoundError(f"Missing {BOUNDARY_FILE}")

    data = json.loads(BOUNDARY_FILE.read_text(encoding="utf-8"))
    features = data.get("features", [])
    if not features:
        raise RuntimeError("Boundary GeoJSON contains no features.")

    # Prefer the actual Augsburg admin relation feature.
    candidates = []
    for feature in features:
        props = feature.get("properties", {})
        if (
            props.get("name") == "Augsburg"
            and props.get("boundary") == "administrative"
            and str(props.get("admin_level")) == "6"
        ):
            candidates.append(feature)

    if not candidates:
        # Fallback for Overpass Turbo exports that may expose relation metadata
        # on associated label/admin-centre features.
        for feature in features:
            props = feature.get("properties", {})
            if props.get("@id") == "relation/62407":
                candidates.append(feature)

    if not candidates:
        # Last-resort: largest polygonal feature in the file.
        candidates = [
            f for f in features
            if f.get("geometry", {}).get("type") in {"Polygon", "MultiPolygon"}
        ]

    if not candidates:
        raise RuntimeError("Could not identify the Augsburg municipal polygon.")

    geoms = [shape(f["geometry"]) for f in candidates if f.get("geometry")]
    polygonal = [g for g in geoms if g.geom_type in {"Polygon", "MultiPolygon"}]
    if not polygonal:
        raise RuntimeError("Selected Augsburg feature has no polygon geometry.")

    boundary = max(polygonal, key=lambda g: g.area)
    if not boundary.is_valid:
        boundary = boundary.buffer(0)

    gdf = gpd.GeoDataFrame(
        [{"name": "Augsburg", "osm_relation": 62407}],
        geometry=[boundary],
        crs="EPSG:4326",
    )

    gdf_utm = gdf.to_crs("EPSG:32632")
    area_km2 = float(gdf_utm.geometry.area.iloc[0] / 1e6)

    gdf.to_file(PROC / "augsburg_municipal_boundary.geojson", driver="GeoJSON")
    gdf_utm.to_file(PROC / "augsburg_municipal_boundary.gpkg", layer="boundary", driver="GPKG")

    return boundary, area_km2


def stream_osm(osm_path):
    """Read only nodes and ways from an OSM XML file using low-memory streaming."""
    if not osm_path.exists():
        raise FileNotFoundError(f"Missing {osm_path}")

    nodes = {}
    ways = []

    # OSM exports conventionally list nodes before ways, so the node dictionary
    # is available when ways are processed.
    for event, elem in ET.iterparse(osm_path, events=("end",)):
        if elem.tag == "node":
            node_id = int(elem.attrib["id"])
            nodes[node_id] = (
                float(elem.attrib["lon"]),
                float(elem.attrib["lat"]),
            )
            elem.clear()

        elif elem.tag == "way":
            way_id = int(elem.attrib["id"])
            refs = [
                int(child.attrib["ref"])
                for child in elem
                if child.tag == "nd"
            ]
            tags = {
                child.attrib["k"]: child.attrib["v"]
                for child in elem
                if child.tag == "tag"
            }
            ways.append((way_id, refs, tags))
            elem.clear()

    return nodes, ways


def is_walkable(tags):
    highway = tags.get("highway")
    if not highway:
        return False

    if highway in EXCLUDED_HIGHWAYS:
        return False

    if tags.get("foot") == "no":
        return False

    if tags.get("access") in EXCLUDED_ACCESS:
        return False

    # Polygons tagged highway=pedestrian + area=yes represent pedestrian areas,
    # not routable centre lines. Keep their boundary out of the routing graph.
    if tags.get("area") == "yes":
        return False

    return True


def main():
    boundary_wgs, area_km2 = load_boundary()
    print(f"Augsburg municipal boundary: {area_km2:.2f} km²")
    print("Streaming OSM XML...")
    osm_nodes, osm_ways = stream_osm(OSM_FILE)

    print(f"OSM nodes read: {len(osm_nodes):,}")
    print(f"OSM ways read: {len(osm_ways):,}")

    transformer = Transformer.from_crs(
        "EPSG:4326", "EPSG:32632", always_xy=True
    )

    node_lookup = {}
    node_rows = []
    edge_rows = []
    edge_id = 0
    accepted_way_count = 0
    rejected_area_way_count = 0

    def graph_node_id(x, y):
        """Return a graph-node id keyed by metric coordinates.

        Coordinate-based keys are necessary because exact polygon clipping can
        create new vertices at the municipal boundary that do not have an
        original OSM node id.
        """
        key = (round(float(x), 3), round(float(y), 3))
        if key in node_lookup:
            return node_lookup[key]

        gid = len(node_lookup)
        node_lookup[key] = gid
        node_rows.append(
            {
                "node_id": gid,
                "x": key[0],
                "y": key[1],
            }
        )
        return gid

    for way_id, refs, tags in osm_ways:
        if tags.get("area") == "yes" and tags.get("highway"):
            rejected_area_way_count += 1

        if not is_walkable(tags):
            continue

        coords = []
        for ref in refs:
            if ref in osm_nodes:
                coords.append(osm_nodes[ref])

        if len(coords) < 2:
            continue

        accepted_way_count += 1

        for a, b in zip(coords[:-1], coords[1:]):
            # Build each raw OSM segment in WGS84 and apply an exact geometric
            # intersection with the municipal polygon. This is the analytical
            # clip; no rectangular extent or midpoint approximation is used.
            raw_segment = LineString([a, b])
            clipped = raw_segment.intersection(boundary_wgs)

            if clipped.is_empty:
                continue

            if clipped.geom_type == "LineString":
                pieces = [clipped]
            elif clipped.geom_type == "MultiLineString":
                pieces = list(clipped.geoms)
            else:
                # Point-only contact with the boundary does not form an edge.
                continue

            for piece_wgs in pieces:
                if piece_wgs.length == 0:
                    continue

                piece_utm = shapely_transform(transformer.transform, piece_wgs)
                length_m = float(piece_utm.length)
                if length_m <= 0:
                    continue

                coords_utm = list(piece_utm.coords)
                x1, y1 = coords_utm[0][:2]
                x2, y2 = coords_utm[-1][:2]

                u = graph_node_id(x1, y1)
                v = graph_node_id(x2, y2)
                if u == v:
                    continue

                edge_rows.append(
                    {
                        "edge_id": edge_id,
                        "osm_way_id": way_id,
                        "u": u,
                        "v": v,
                        "length_m": length_m,
                        "highway": tags.get("highway"),
                        "name": tags.get("name"),
                        "surface": tags.get("surface"),
                        "smoothness": tags.get("smoothness"),
                        "incline": tags.get("incline"),
                        "lit": tags.get("lit"),
                        "crossing": tags.get("crossing"),
                        "step_count": tags.get("step_count"),
                        "tunnel": tags.get("tunnel"),
                        "bridge": tags.get("bridge"),
                        "geometry": piece_utm,
                    }
                )
                edge_id += 1

    if not node_rows or not edge_rows:
        raise RuntimeError("No routable graph was created.")

    nodes = gpd.GeoDataFrame(
        node_rows,
        geometry=[Point(r["x"], r["y"]) for r in node_rows],
        crs="EPSG:32632",
    )

    edges = gpd.GeoDataFrame(
        edge_rows,
        geometry="geometry",
        crs="EPSG:32632",
    )

    nodes.to_file(PROC / "network_nodes.gpkg", layer="nodes", driver="GPKG")
    edges.to_file(PROC / "network_edges.gpkg", layer="edges", driver="GPKG")

    attr_summary = pd.DataFrame(
        {
            "attribute": [
                "surface",
                "smoothness",
                "incline",
                "lit",
                "step_count",
            ],
            "non_null_edges": [
                edges["surface"].notna().sum(),
                edges["smoothness"].notna().sum(),
                edges["incline"].notna().sum(),
                edges["lit"].notna().sum(),
                edges["step_count"].notna().sum(),
            ],
        }
    )
    attr_summary["coverage_pct"] = (
        attr_summary["non_null_edges"] / len(edges) * 100
    )
    attr_summary.to_csv(
        PROC / "network_attribute_completeness.csv",
        index=False,
    )

    summary = pd.DataFrame(
        {
            "metric": [
                "municipal_boundary_area_km2",
                "osm_nodes_read",
                "osm_ways_read",
                "accepted_walkable_ways",
                "excluded_highway_area_ways",
                "network_nodes",
                "network_edges",
                "total_edge_length_km",
            ],
            "value": [
                area_km2,
                len(osm_nodes),
                len(osm_ways),
                accepted_way_count,
                rejected_area_way_count,
                len(nodes),
                len(edges),
                edges["length_m"].sum() / 1000,
            ],
        }
    )

    summary.to_csv(PROC / "network_build_summary.csv", index=False)
    print(summary.to_string(index=False))
    print("\nAttribute completeness:")
    print(attr_summary.to_string(index=False))


if __name__ == "__main__":
    main()
