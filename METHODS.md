# Methodology

## 1. Study area

The study area is the Augsburg municipal administrative boundary, represented by
OpenStreetMap relation 62407 (`admin_level=6`).

The analysis does not use a rectangular final extent. OSM line segments are
intersected with the actual municipal polygon.

## 2. Network source

The pedestrian network is obtained from an Augsburg-specific Overpass query.

Candidate OSM ways require a `highway` tag. Obvious motorway/trunk/construction
classes, `foot=no`, and `access=private` or `access=no` are excluded. Ways tagged
`area=yes` are excluded from the routable graph because polygon rings do not
represent meaningful route centre lines.

## 3. Graph construction

OSM way segments are projected to EPSG:32632 and converted to an undirected
NetworkX graph. Edge weight is physical segment length in metres.

## 4. Connectivity

The full graph is decomposed into connected components. The number and size of
components are reported as data-quality diagnostics.

Accessibility calculations use the largest connected component. This prevents
small disconnected mapping fragments from dominating shortest-path results.

## 5. Supermarket snapping

Supermarket coordinates are projected to EPSG:32632 and snapped to the nearest
node in the analysed graph component.

The snap distance is explicitly reported for every store.

A virtual store source is connected to the snapped graph node using the snap
distance as edge cost. Therefore network distance is measured from the actual
store point rather than from the snapped node.

## 6. Network accessibility

Multi-source Dijkstra calculates shortest network distance from each analysed
graph node to the nearest sampled supermarket.

Walking time is estimated from network distance using a fixed reference speed of
80 m/min (4.8 km/h).

## 7. Euclidean comparison

For the same graph nodes, Euclidean distance is measured to the actual
supermarket coordinates.

The central diagnostic is:

```text
detour ratio = network distance / Euclidean distance
```

Ratios are not interpreted for nodes within 50 m Euclidean distance of a store,
because the denominator becomes unstable near zero.

## 8. OSM network attributes

Attributes such as `surface`, `smoothness`, `incline`, `lit`, `step_count`,
crossings, tunnels and bridges are retained when available.

Project03 reports their completeness but does not assign undocumented penalty
weights. The baseline routing cost remains physical distance.

## 9. Interpretation

The model describes pedestrian-network accessibility under the mapped OSM
network. It is not an observed pedestrian travel-time or behavioural model.


## 10. Cumulative walking-accessibility figure

The walking-accessibility figure uses an empirical cumulative distribution
function (ECDF). For each walking-time threshold, the y-axis reports the share
of **analysed graph nodes** whose network distance to one of the sampled
supermarkets falls within that threshold.

This is a graph-node statistic. It is not interpreted as population coverage,
area coverage, household coverage or network-length coverage.
