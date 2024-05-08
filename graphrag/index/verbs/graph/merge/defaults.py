# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing DEFAULT_NODE_OPERATIONS, DEFAULT_EDGE_OPERATIONS and DEFAULT_CONCAT_SEPARATOR values definition."""

from .typing import BasicMergeOperation

DEFAULT_NODE_OPERATIONS = {
    "*": {
        "operation": BasicMergeOperation.Replace,
    }
}

DEFAULT_EDGE_OPERATIONS = {
    "*": {
        "operation": BasicMergeOperation.Replace,
    },
    "weight": "sum",
}

DEFAULT_CONCAT_SEPARATOR = ","
