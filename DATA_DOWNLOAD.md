# Project03 input data

Project03 no longer requires the full Schwaben PBF during normal reproduction.

Two Augsburg-specific Overpass exports are used:

```text
data/raw/augsburg_boundary.geojson
data/raw/augsburg_pedestrian_network.osm
```

## Municipal boundary

The study area is OpenStreetMap relation `62407`:

- name: Augsburg
- boundary: administrative
- admin_level: 6
- official municipality code: 09761000

The polygon is used as the final analytical boundary.

## Pedestrian network

The OSM XML was generated from an Overpass area query based on relation 62407.

Included ways have a `highway` tag, while obvious motorway/trunk/construction classes,
`foot=no`, and `access=private` were excluded at query time.

The Python pipeline applies a second validation/filtering stage and excludes
`area=yes` pedestrian polygons from the routable graph.

## Attribution

OpenStreetMap data © OpenStreetMap contributors, ODbL.
