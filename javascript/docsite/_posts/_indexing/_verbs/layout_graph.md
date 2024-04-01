---
title: layout_graph
navtitle: layout_graph
layout: page
tags: [post, verb]
---
Apply a layout algorithm to a graph. The graph is expected to be in graphml format. The verb outputs a new column containing the layed out graph.

## Usage
```yaml
verb: layout_graph
args:
    graph_column: clustered_graph # The name of the column containing the graph, should be a graphml graph
    embeddings_column: embeddings # The name of the column containing the embeddings
    to: node_positions # The name of the column to output the node positions to
    graph_to: positioned_graph # The name of the column to output the positioned graph to
    strategy: <strategy config> # See strategies section below
```

## Strategies
The layout graph verb uses a strategy to layout the graph. The strategy is a json object which defines the strategy to use. The following strategies are available:

### umap
This strategy uses the umap algorithm to layout a graph. The strategy config is as follows:
```yaml
strategy:
    type: umap
    n_neighbors: 5 # Optional, The number of neighbors to use for the umap algorithm, default: 5
    min_dist: 0.75 # Optional, The min distance to use for the umap algorithm, default: 0.75
```

## Code
[layout_graph.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/graph/layout/layout_graph.py)