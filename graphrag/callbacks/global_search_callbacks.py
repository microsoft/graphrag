# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""GlobalSearch LLM Callbacks."""

from graphrag.callbacks.llm_callbacks import BaseLLMCallback
from graphrag.query.structured_search.base import SearchResult


class GlobalSearchLLMCallback(BaseLLMCallback):
    """GlobalSearch LLM Callbacks."""

    def __init__(self):
        super().__init__()
        self.map_response_contexts = []
        self.map_response_outputs = []

    def on_map_response_start(self, map_response_contexts: list[str]):
        """Handle the start of map response."""
        self.map_response_contexts = map_response_contexts

    def on_map_response_end(self, map_response_outputs: list[SearchResult]):
        """Handle the end of map response."""
        self.map_response_outputs = map_response_outputs
