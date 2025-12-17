# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'Chunker' class."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import nltk
from graphrag_common.factory.factory import Factory, ServiceScope

from graphrag.chunking.bootstrap import bootstrap
from graphrag.config.enums import ChunkStrategyType
from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.index.text_splitting.text_splitting import (
    split_single_text_on_tokens,
)
from graphrag.tokenizer.get_tokenizer import get_tokenizer


class Chunker(ABC):
    """Abstract base class for text chunkers."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Create a chunker instance."""

    @abstractmethod
    def chunk(self, text: str) -> list[str]:
        """Chunk method definition."""


class TokenChunker(Chunker):
    """A chunker that splits text into token-based chunks."""

    def __init__(
        self,
        size: int,
        overlap: int,
        encoding_model: str,
        **kwargs: Any,
    ) -> None:
        """Create a token chunker instance."""
        self._size = size
        self._overlap = overlap
        self._encoding_model = encoding_model

    def chunk(self, text: str) -> list[str]:
        """Chunk the text into token-based chunks."""
        tokenizer = get_tokenizer(encoding_model=self._encoding_model)
        return split_single_text_on_tokens(
            text,
            chunk_overlap=self._overlap,
            tokens_per_chunk=self._size,
            encode=tokenizer.encode,
            decode=tokenizer.decode,
        )


class SentenceChunker(Chunker):
    """A chunker that splits text into sentence-based chunks."""

    def __init__(self, **kwargs: Any) -> None:
        """Create a sentence chunker instance."""
        bootstrap()

    def chunk(self, text: str) -> list[str]:
        """Chunk the text into sentence-based chunks."""
        return nltk.sent_tokenize(text)


class ChunkerFactory(Factory[Chunker]):
    """Factory for creating Chunker instances."""


chunker_factory = ChunkerFactory()


def register_chunker(
    chunker_type: str,
    chunker_initializer: Callable[..., Chunker],
    scope: ServiceScope = "transient",
) -> None:
    """Register a custom chunker implementation.

    Args
    ----
        - chunker_type: str
            The chunker id to register.
        - chunker_initializer: Callable[..., Chunker]
            The chunker initializer to register.
    """
    chunker_factory.register(chunker_type, chunker_initializer, scope)


def create_chunker(config: ChunkingConfig) -> Chunker:
    """Create a chunker implementation based on the given configuration.

    Args
    ----
        - config: ChunkingConfig
            The chunker configuration to use.

    Returns
    -------
        Chunker
            The created chunker implementation.
    """
    config_model = config.model_dump()
    chunker_strategy = config.strategy

    if chunker_strategy not in chunker_factory:
        match chunker_strategy:
            case ChunkStrategyType.tokens:
                chunker_factory.register(ChunkStrategyType.tokens, TokenChunker)
            case ChunkStrategyType.sentence:
                chunker_factory.register(ChunkStrategyType.sentence, SentenceChunker)
            case _:
                msg = f"ChunkingConfig.strategy '{chunker_strategy}' is not registered in the ChunkerFactory. Registered types: {', '.join(chunker_factory.keys())}."
                raise ValueError(msg)

    return chunker_factory.create(chunker_strategy, init_args=config_model)
