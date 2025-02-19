# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LLMFactory Tests.

These tests will test the LLMFactory class and the creation of custom and provided LLMs.
"""

from graphrag.llm.factory import LLMFactory
from graphrag.llm.manager import LLMManager
from graphrag.llm.response.base import BaseLLMOutput, BaseLLMResponse, LLMResponse


async def test_create_custom_chat_llm():
    class CustomChatLLM:
        def __init__(self, **kwargs):
            pass

        async def chat(self, prompt: str, **kwargs) -> LLMResponse:
            return BaseLLMResponse(output=BaseLLMOutput(content="content"))

    LLMFactory.register_chat("custom_chat", CustomChatLLM)
    llm = LLMManager().get_or_create_chat_llm("custom", "custom_chat")
    assert isinstance(llm, CustomChatLLM)
    response = await llm.chat("prompt")
    assert response.output.content == "content"


async def test_create_custom_embedding_llm():
    class CustomEmbeddingLLM:
        def __init__(self, **kwargs):
            pass

        async def embed(self, text: str | list[str], **kwargs) -> list[list[float]]:
            return [[1.0]]

    LLMFactory.register_embedding("custom_embedding", CustomEmbeddingLLM)
    llm = LLMManager().get_or_create_embedding_llm("custom", "custom_embedding")
    assert isinstance(llm, CustomEmbeddingLLM)
    response = await llm.embed("text")
    assert response == [[1.0]]
