---
title: cluster_graph
navtitle: cluster_graph
layout: page
tags: [post, verb]
---
Apply a hierarchical clustering algorithm to a graph. The graph is expected to be in graphml format. The verb outputs a new column containing the clustered graph, and a new column containing the level of the graph.

## Usage
```yaml
verb: cluster_graph
args:
    column: entity_graph # The name of the column containing the graph, should be a graphml graph
    to: clustered_graph # The name of the column to output the clustered graph to
    level_to: level # The name of the column to output the level to
    strategy: <strategy config> # See strategies section below
```

## Strategies
The cluster graph verb uses a strategy to cluster the graph. The strategy is a json object which defines the strategy to use. The following strategies are available:

### leiden
This strategy uses the leiden algorithm to cluster a graph. The strategy config is as follows:
```yaml
strategy:
    type: leiden
    max_cluster_size: 10 # Optional, The max cluster size to use, default: 10
    use_lcc: true # Optional, if the largest connected component should be used with the leiden algorithm, default: true
    seed: 0xDEADBEEF # Optional, the seed to use for the leiden algorithm, default: 0xDEADBEEF
    levels: [0, 1] # Optional, the levels to output, default: all the levels detected

```

## Code
[cluster_graph.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/graph/clustering/cluster_graph.py)