# Methodology

## 1. Study area

The analytical study area is the municipal administrative boundary of Augsburg,
represented by OpenStreetMap relation 62407 (`admin_level=6`).

The project does not use a rectangular study extent for final analysis. Each candidate OSM line segment is clipped by exact geometric intersection with the Augsburg municipal polygon; boundary intersections become graph vertices.

## 2. Network source

The network is an Augsburg-specific Overpass export containing OSM ways with
`highway` tags that are potentially usable by pedestrians.

The export is parsed directly from OSM XML using a streaming parser so that the
workflow remains lightweight.

## 3. Routing graph

OSM ways are converted into graph edges between consecutive OSM nodes.

Edge length is measured in UTM zone 32N (`EPSG:32632`).

Pedestrian polygons (`area=yes`) are excluded from the graph because their
boundary rings do not represent meaningful route centre lines.

## 4. Connectivity

The accessibility stage retains the largest connected pedestrian-network
component before shortest-path analysis. The size of excluded components is
reported as a data-quality diagnostic.

## 5. Supermarket snapping

Each supermarket is projected to the same metric CRS and snapped to the nearest
network node. Snap distances are reported; unusually large snap distances must
be investigated rather than silently accepted.

## 6. Network accessibility

Multi-source Dijkstra calculates the shortest network distance from all network
nodes to the nearest sampled supermarket.

Walking time is estimated using a fixed reference speed of 4.8 km/h. It is a
comparative accessibility indicator, not an observed travel-time model.

## 7. Euclidean comparison

For the same network nodes, Euclidean distance to the nearest sampled store is
calculated.

The main diagnostic is:

`detour ratio = network distance / Euclidean distance`

Nodes very close to a supermarket are excluded from detour-ratio interpretation
because the denominator approaches zero.

## 8. Additional network-quality information

The OSM export contains attributes such as `surface`, `smoothness`, `incline`,
`lit`, `steps`, crossings, tunnels and bridges for parts of the network.

Project03 reports the completeness of these fields. They are not assigned
arbitrary penalty weights in the baseline routing model.

This leaves a transparent extension path for a later generalized-cost routing
model without pretending that undocumented weights are empirically validated.
