#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Common types for the GraphRAG knowledge model."""
from collections.abc import Callable

TextEmbedder = Callable[[str], list[float]]
