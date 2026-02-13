# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing snapshot_graphml method definition."""

import networkx as nx
import pandas as pd
from graphrag_storage import Storage


async def snapshot_graphml(
    edges: pd.DataFrame,
    name: str,
    storage: Storage,
) -> None:
    """Take a entire snapshot of a graph to standard graphml format."""
    graph = nx.from_pandas_edgelist(edges, edge_attr=["weight"])
    graphml = "\n".join(nx.generate_graphml(graph))
    await storage.set(name + ".graphml", graphml)
