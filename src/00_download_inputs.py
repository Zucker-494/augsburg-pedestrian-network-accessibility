"""Download the two public OSM inputs required by Project03.

This script is intended both for local reproduction and GitHub Actions.

Boundary:
    Nominatim lookup of OSM relation 62407 with polygon geometry.

Pedestrian network:
    Overpass QL query constrained to the Augsburg administrative area.

OpenStreetMap data: © OpenStreetMap contributors, ODbL.
"""

from pathlib import Path
import time
import requests

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

BOUNDARY_OUT = RAW / "augsburg_boundary.geojson"
NETWORK_OUT = RAW / "augsburg_pedestrian_network.osm"

USER_AGENT = (
    "Project03-Augsburg-Network-Accessibility/1.0 "
    "(GIS portfolio reproducibility workflow)"
)

BOUNDARY_URL = (
    "https://nominatim.openstreetmap.org/lookup"
    "?osm_ids=R62407"
    "&format=geojson"
    "&polygon_geojson=1"
)

OVERPASS_QUERY = """
[out:xml][timeout:300];

relation(62407);
map_to_area->.augsburg;

(
  way(area.augsburg)
    ["highway"]
    ["highway"!~"motorway|motorway_link|trunk|trunk_link|raceway|construction|proposed"]
    ["foot"!="no"]
    ["access"!="private"];
);

(._;>;);

out body;
""".strip()

OVERPASS_ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


def download_boundary():
    print("Downloading Augsburg municipal boundary (OSM relation 62407)...")
    response = requests.get(
        BOUNDARY_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=120,
    )
    response.raise_for_status()

    data = response.content
    if len(data) < 1000:
        raise RuntimeError("Boundary response is unexpectedly small.")

    BOUNDARY_OUT.write_bytes(data)
    print(f"Boundary saved: {BOUNDARY_OUT} ({len(data):,} bytes)")


def download_network():
    errors = []

    for endpoint in OVERPASS_ENDPOINTS:
        print(f"Querying pedestrian network via {endpoint} ...")
        try:
            response = requests.post(
                endpoint,
                data={"data": OVERPASS_QUERY},
                headers={"User-Agent": USER_AGENT},
                timeout=420,
            )
            response.raise_for_status()

            data = response.content

            if not data.lstrip().startswith(b"<?xml"):
                raise RuntimeError("Overpass response is not OSM XML.")

            if b"<way " not in data or b"<node " not in data:
                raise RuntimeError("Overpass response lacks node/way topology.")

            NETWORK_OUT.write_bytes(data)
            print(
                f"Network saved: {NETWORK_OUT} "
                f"({len(data)/1024/1024:.1f} MB)"
            )
            return

        except Exception as exc:
            errors.append(f"{endpoint}: {exc}")
            print(f"Endpoint failed: {exc}")
            time.sleep(3)

    raise RuntimeError(
        "All Overpass endpoints failed:\n" + "\n".join(errors)
    )


def main():
    download_boundary()
    download_network()

    print("\nProject03 raw inputs are ready.")
    print(f"  {BOUNDARY_OUT.relative_to(BASE)}")
    print(f"  {NETWORK_OUT.relative_to(BASE)}")


if __name__ == "__main__":
    main()
