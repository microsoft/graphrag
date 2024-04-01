#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

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
