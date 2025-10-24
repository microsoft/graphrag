# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing a factory for supported llm types."""

from graphrag_factory import Factory

from graphrag.config.enums import ModelType
from graphrag.language_model.protocol.base import ChatModel, EmbeddingModel
from graphrag.language_model.providers.litellm.chat_model import LitellmChatModel
from graphrag.language_model.providers.litellm.embedding_model import (
    LitellmEmbeddingModel,
)


class ChatModelFactory(Factory[ChatModel]):
    """Singleton factory for creating ChatModel instances."""


class EmbeddingModelFactory(Factory[EmbeddingModel]):
    """Singleton factory for creating EmbeddingModel instances."""


# --- Register default implementations ---
ChatModelFactory().register(ModelType.Chat, LitellmChatModel)
EmbeddingModelFactory().register(ModelType.Embedding, LitellmEmbeddingModel)
