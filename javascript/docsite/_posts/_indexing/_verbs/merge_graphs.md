---
title: merge_graphs
navtitle: merge_graphs
layout: page
tags: [post, verb]
---
Merge multiple graphs together. The graphs are expected to be in graphml format. The verb outputs a new column containing the merged graph.

> Note: This will merge all rows into a single graph.

## Usage
```yaml
verb: merge_graph
args:
    column: clustered_graph # The name of the column containing the graph, should be a graphml graph
    to: merged_graph # The name of the column to output the merged graph to
    nodes: <node operations> # See node operations section below
    edges: <edge operations> # See edge operations section below
```

## Node Operations
The merge graph verb can perform operations on the nodes of the graph.

### Usage
```yaml
nodes:
    <attribute name>: <operation>
    ... for each attribute or use the special value "*" for all attributes
```

## Edge Operations
The merge graph verb can perform operations on the nodes of the graph.

### Usage
```yaml
edges:
    <attribute name>: <operation>
    ... for each attribute or use the special value "*" for all attributes
```

## Operations
The merge graph verb can perform operations on the nodes and edges of the graph. The following operations are available:

- __replace__: This operation replaces the attribute with the last value seen.
- __skip__: This operation skips the attribute, and just uses the first value seen.
- __concat__: This operation concatenates the attribute with the last value seen.
- __sum__: This operation sums the attribute with the last value seen.
- __max__: This operation takes the max of the attribute with the last value seen.
max
- __min__: This operation takes the min of the attribute with the last value seen.
- __average__: This operation takes the mean of the attribute with the last value seen.
- __multiply__: This operation multiplies the attribute with the last value seen.

## Code
[merge_graphs.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/graph/merge/merge_graphs.py)