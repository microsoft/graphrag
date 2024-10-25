# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing snapshot method definition."""

import networkx as nx

from graphrag.index.storage.pipeline_storage import PipelineStorage


async def snapshot_graphml(
    input: str | nx.Graph,
    name: str,
    storage: PipelineStorage,
) -> None:
    """Take a entire snapshot of a graph to standard graphml format."""
    graphml = input if isinstance(input, str) else "\n".join(nx.generate_graphml(input))
    await storage.set(name + ".graphml", graphml)
