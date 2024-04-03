---
title: create_graph
navtitle: create_graph
layout: page
tags: [post, verb]
---
Create a graph from a dataframe. The verb outputs a new column containing the graph.

> Note: This will roll up all rows into a single graph.

## Usage
```yaml
verb: create_graph
args:
    type: node # The type of graph to create, one of: node, edge
    to: <column name> # The name of the column to output the graph to, this will be a graphml graph
    attributes: # The attributes for the nodes / edges
        # If using the node type, the following attributes are required:
        id: <id_column_name>

        # If using the edge type, the following attributes are required:
        source: <source_column_name>
        target: <target_column_name>

        # Other attributes can be added as follows:
        <attribute_name>: <column_name>
        ... for each attribute
```

## Code
[create.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/graph/create.py)