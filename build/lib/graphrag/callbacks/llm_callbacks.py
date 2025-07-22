# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM Callbacks."""

from typing import Protocol


class BaseLLMCallback(Protocol):
    """Base class for LLM callbacks."""

    def on_llm_new_token(self, token: str):
        """Handle when a new token is generated."""
        ...
