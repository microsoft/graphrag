#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Topological sort utility method."""
from graphlib import TopologicalSorter


def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """Topological sort."""
    ts = TopologicalSorter(graph)
    return list(ts.static_order())
