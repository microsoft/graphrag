---
title: unpack_graph
navtitle: unpack_graph
layout: page
tags: [post, verb]
---
Unpack nodes or edges from a graphml graph, into a list of nodes or edges.

This verb will create columns for each attribute in a node or edge.

## Usage
```yaml
verb: unpack_graph
args:
    type: node # The type of data to unpack, one of: node, edge. node will create a node list, edge will create an edge list
    column: <column name> # The name of the column containing the graph, should be a graphml graph
```

## Code
[unpack.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/graph/unpack.py)