# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LLMFactory Tests.

These tests will test the LLMFactory class and the creation of custom and provided LLMs.
"""

from collections.abc import AsyncGenerator, Generator
from typing import Any

from graphrag.language_model.factory import ModelFactory
from graphrag.language_model.manager import ModelManager
from graphrag.language_model.response.base import (
    BaseModelOutput,
    BaseModelResponse,
    ModelResponse,
)


async def test_create_custom_chat_model():
    class CustomChatModel:
        config: Any

        def __init__(self, **kwargs):
            pass

        async def achat(
            self, prompt: str, history: list | None = None, **kwargs: Any
        ) -> ModelResponse:
            return BaseModelResponse(output=BaseModelOutput(content="content"))

        def chat(
            self, prompt: str, history: list | None = None, **kwargs: Any
        ) -> ModelResponse:
            return BaseModelResponse(output=BaseModelOutput(content="content"))

        async def achat_stream(
            self, prompt: str, history: list | None = None, **kwargs: Any
        ) -> AsyncGenerator[str, None]:
            yield ""

        def chat_stream(
            self, prompt: str, history: list | None = None, **kwargs: Any
        ) -> Generator[str, None]: ...

    ModelFactory.register_chat("custom_chat", CustomChatModel)
    model = ModelManager().get_or_create_chat_model("custom", "custom_chat")
    assert isinstance(model, CustomChatModel)
    response = await model.achat("prompt")
    assert response.output.content == "content"

    response = model.chat("prompt")
    assert response.output.content == "content"


async def test_create_custom_embedding_llm():
    class CustomEmbeddingModel:
        config: Any

        def __init__(self, **kwargs):
            pass

        async def aembed(self, text: str, **kwargs) -> list[float]:
            return [1.0]

        def embed(self, text: str, **kwargs) -> list[float]:
            return [1.0]

        async def aembed_batch(
            self, text_list: list[str], **kwargs
        ) -> list[list[float]]:
            return [[1.0]]

        def embed_batch(self, text_list: list[str], **kwargs) -> list[list[float]]:
            return [[1.0]]

    ModelFactory.register_embedding("custom_embedding", CustomEmbeddingModel)
    llm = ModelManager().get_or_create_embedding_model("custom", "custom_embedding")
    assert isinstance(llm, CustomEmbeddingModel)
    response = await llm.aembed("text")
    assert response == [1.0]

    response = llm.embed("text")
    assert response == [1.0]

    response = await llm.aembed_batch(["text"])
    assert response == [[1.0]]

    response = llm.embed_batch(["text"])
    assert response == [[1.0]]
