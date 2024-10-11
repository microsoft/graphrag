# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM Callbacks."""


class BaseLLMCallback:
    """Base class for LLM callbacks."""

    def __init__(self):
        self.response = []

    def on_llm_new_token(self, token: str):
        """Handle when a new token is generated."""
        self.response.append(token)
