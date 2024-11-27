# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine graph utils package root."""

from graphrag.index.graph.utils.normalize_node_names import normalize_node_names
from graphrag.index.graph.utils.stable_lcc import stable_largest_connected_component

__all__ = ["normalize_node_names", "stable_largest_connected_component"]
