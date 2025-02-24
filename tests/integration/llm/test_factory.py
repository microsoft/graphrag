# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LLMFactory Tests.

These tests will test the LLMFactory class and the creation of custom and provided LLMs.
"""

from graphrag.language_model.factory import ModelFactory
from graphrag.language_model.manager import ModelManager
from graphrag.language_model.response.base import (
    BaseModelOutput,
    BaseModelResponse,
    ModelResponse,
)


async def test_create_custom_chat_llm():
    class CustomChatLLM:
        def __init__(self, **kwargs):
            pass

        async def chat(self, prompt: str, **kwargs) -> ModelResponse:
            return BaseModelResponse(output=BaseModelOutput(content="content"))

    ModelFactory.register_chat("custom_chat", CustomChatLLM)
    llm = ModelManager().get_or_create_chat_model("custom", "custom_chat")
    assert isinstance(llm, CustomChatLLM)
    response = await llm.chat("prompt")
    assert response.output.content == "content"


async def test_create_custom_embedding_llm():
    class CustomEmbeddingLLM:
        def __init__(self, **kwargs):
            pass

        async def embed(self, text: str | list[str], **kwargs) -> list[list[float]]:
            return [[1.0]]

    ModelFactory.register_embedding("custom_embedding", CustomEmbeddingLLM)
    llm = ModelManager().get_or_create_embedding_model("custom", "custom_embedding")
    assert isinstance(llm, CustomEmbeddingLLM)
    response = await llm.embed("text")
    assert response == [[1.0]]
