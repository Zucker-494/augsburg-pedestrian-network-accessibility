# Project03 Results Summary

This file is generated automatically by the reproducible Project03 pipeline.

## Study area and network

- Augsburg municipal area: **146.76 km²**
- Raw routable network nodes: **146,290**
- Raw routable network edges: **163,497**
- Total represented edge length: **2,839.6 km**
- Connected components: **808**
- Largest-component share: **97.48%**

## Accessibility

- Analysed graph nodes: **142,606**
- Median Euclidean distance: **1.61 km**
- Median pedestrian-network distance: **2.15 km**
- P90 pedestrian-network distance: **5.16 km**
- Median detour ratio: **1.27**
- P90 detour ratio: **1.63**
- Network nodes within 10 min: **15.7%**
- Network nodes within 15 min: **28.8%**

## Snapping QA

Maximum supermarket-to-network snap distance:

**47.8 m — Kaufland Augsburg-Oberhausen**

The network-distance calculation includes this store-to-network connector, so
the comparison is made from the actual supermarket point rather than treating
the snapped network node as the supermarket itself.

## Interpretation boundary

These results refer to the current sampled supermarkets and the OSM pedestrian-network representation.

Walking time is derived from network distance using a fixed reference speed of
4.8 km/h. It is a comparative accessibility indicator, not an observed
pedestrian travel-time model.
