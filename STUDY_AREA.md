# Study Area

Project03 uses the **municipal administrative boundary of Augsburg** as its
analytical study area.

## Operational boundary

The boundary is OpenStreetMap relation **62407**:

```text
name=Augsburg
boundary=administrative
admin_level=6
```

The cloud workflow downloads this relation as GeoJSON.

## Spatial clipping rule

The analytical network is not clipped by a rectangle.

Each OSM road segment is geometrically intersected with the Augsburg municipal
polygon. If a segment crosses the administrative boundary, the intersection
point becomes the end point of the retained graph segment.

A rectangular extent is therefore not used to define any final network result.

## Coordinate reference system

Input OSM geometries use WGS84 (`EPSG:4326`). Distance and graph-edge length are
calculated after projection to ETRS89 / UTM zone 32N (`EPSG:32632`).
