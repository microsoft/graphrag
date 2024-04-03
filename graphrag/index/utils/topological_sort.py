# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Topological sort utility method."""

from graphlib import TopologicalSorter


def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """Topological sort."""
    ts = TopologicalSorter(graph)
    return list(ts.static_order())
