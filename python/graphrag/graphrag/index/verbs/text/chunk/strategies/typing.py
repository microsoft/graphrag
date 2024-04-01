#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing ChunkStrategy definition."""
from collections.abc import Callable, Iterable
from typing import Any

from datashaper import ProgressTicker

from graphrag.index.verbs.text.chunk.typing import TextChunk

# Given a list of document texts, return a list of tuples of (source_doc_indices, text_chunk)

ChunkStrategy = Callable[
    [list[str], dict[str, Any], ProgressTicker], Iterable[TextChunk]
]
