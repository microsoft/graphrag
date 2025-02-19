# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""No-op Query Callbacks."""

from typing import Any

from graphrag.callbacks.query_callbacks import QueryCallbacks
from graphrag.query.structured_search.base import SearchResult


class NoopQueryCallbacks(QueryCallbacks):
    """A no-op implementation of QueryCallbacks."""

    def on_context(self, context: Any) -> None:
        """Handle when context data is constructed."""

    def on_map_response_start(self, map_response_contexts: list[str]) -> None:
        """Handle the start of map operation."""

    def on_map_response_end(self, map_response_outputs: list[SearchResult]) -> None:
        """Handle the end of map operation."""

    def on_reduce_response_start(
        self, reduce_response_context: str | dict[str, Any]
    ) -> None:
        """Handle the start of reduce operation."""

    def on_reduce_response_end(self, reduce_response_output: str) -> None:
        """Handle the end of reduce operation."""

    def on_llm_new_token(self, token):
        """Handle when a new token is generated."""
