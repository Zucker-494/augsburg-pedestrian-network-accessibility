# Input Data

Project03 is designed so that no large regional PBF needs to be stored in the
repository.

## 1. Augsburg municipal boundary

The workflow downloads OpenStreetMap relation **62407** as:

```text
data/raw/augsburg_boundary.geojson
```

The feature is validated as:

```text
name=Augsburg
boundary=administrative
admin_level=6
```

## 2. Augsburg pedestrian network

The workflow queries Overpass and stores the result as:

```text
data/raw/augsburg_pedestrian_network.osm
```

The query selects OSM `highway` ways in the Augsburg administrative area while
excluding obvious non-pedestrian classes and explicit access restrictions.

The Python pipeline then performs another validation/filtering stage and applies
the exact Augsburg municipal polygon clip.

## 3. Supermarket sample

The controlled comparison uses:

```text
data/supermarkets_sample.csv
```

The sample is intentionally kept consistent with Project02 so that the main
difference between the projects is the distance representation.

## Data licence

OpenStreetMap data © OpenStreetMap contributors, ODbL.
