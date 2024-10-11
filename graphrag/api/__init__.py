# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""API for GraphRAG.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from .index_api import build_index
from .prompt_tune_api import DocSelectionType, generate_indexing_prompts
from .query_api import (
    global_search,
    global_search_streaming,
    local_search,
    local_search_streaming,
)

__all__ = [  # noqa: RUF022
    # index API
    "build_index",
    # query API
    "global_search",
    "global_search_streaming",
    "local_search",
    "local_search_streaming",
    # prompt tuning API
    "DocSelectionType",
    "generate_indexing_prompts",
]
