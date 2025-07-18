# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""API for GraphRAG.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from graphrag.api.index import build_index
from graphrag.api.prompt_tune import generate_indexing_prompts
from graphrag.api.query import (
    basic_search,
    basic_search_streaming,
    drift_search,
    drift_search_streaming,
    global_search,
    global_search_streaming,
    local_search,
    local_search_streaming,
    multi_index_basic_search,
    multi_index_drift_search,
    multi_index_global_search,
    multi_index_local_search,
)
from graphrag.prompt_tune.types import DocSelectionType

__all__ = [  # noqa: RUF022
    # index API
    "build_index",
    # query API
    "global_search",
    "global_search_streaming",
    "local_search",
    "local_search_streaming",
    "drift_search",
    "drift_search_streaming",
    "basic_search",
    "basic_search_streaming",
    "multi_index_basic_search",
    "multi_index_drift_search",
    "multi_index_global_search",
    "multi_index_local_search",
    # prompt tuning API
    "DocSelectionType",
    "generate_indexing_prompts",
]
