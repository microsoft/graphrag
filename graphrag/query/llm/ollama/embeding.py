# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Ollama Embedding model implementation."""

from typing import Any

from graphrag.llm import OllamaConfiguration, create_ollama_client
from graphrag.query.llm.base import BaseTextEmbedding


class OllamaEmbedding(BaseTextEmbedding):
    """Wrapper for Ollama Embedding models."""

    def __init__(self, configuration: OllamaConfiguration):
        self.configuration = configuration
        self.sync_client = create_ollama_client(configuration, sync=True)
        self.async_client = create_ollama_client(configuration)

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Embed a text string."""
        response = self.sync_client.embed(
            input=text,
            **self.configuration.get_embed_cache_args(),
        )
        return response["embeddings"][0]

    async def aembed(self, text: str, **kwargs: Any) -> list[float]:
        """Embed a text string asynchronously."""
        response = await self.async_client.embed(
            input=text,
            **self.configuration.get_embed_cache_args(),
        )
        return response["embeddings"][0]
