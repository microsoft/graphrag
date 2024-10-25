# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from fnllm import LLM

from graphrag.index.llm.mock_llm import MockChatLLM


def create_mock_llm(
    responses: list[str],
) -> LLM:
    """Creates a mock LLM that returns the given responses."""
    return MockChatLLM(responses)
