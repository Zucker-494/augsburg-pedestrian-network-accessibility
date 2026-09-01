# Study Area Boundary

Project03 uses the **municipal administrative boundary of Augsburg** as the analytical study area.

## Operational source

The pipeline extracts the administrative polygon named `Augsburg` directly from the Geofabrik Schwaben OpenStreetMap PBF. It prefers:

- `boundary=administrative`
- `admin_level=6`

The selected geometry is saved to:

- `data/processed/augsburg_municipal_boundary.geojson`
- `data/processed/augsburg_municipal_boundary.parquet`

## Clipping rule

The road network is clipped with the municipal polygon.

A polygon bounding box is used only to reduce the amount of PBF data read into memory. No analytical result is clipped or summarized by that rectangle.

## Validation

For visual/administrative validation, the Bavarian Surveying Administration publishes ALKIS administrative boundaries. The municipal boundaries are cadastral-derived and available as an official open-data WMS.

The operational vector clip remains OSM-based so the complete workflow can be reproduced from the same Geofabrik source file.
