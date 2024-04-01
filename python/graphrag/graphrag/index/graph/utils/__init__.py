#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine graph utils package root."""
from .normalize_node_names import normalize_node_names
from .stable_lcc import stable_largest_connected_component

__all__ = ["normalize_node_names", "stable_largest_connected_component"]
