# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'ChunkerFactory', 'register_chunker', and 'create_chunker'."""

from collections.abc import Callable

from graphrag_common.factory.factory import Factory, ServiceScope

from graphrag_chunking.chunk_strategy_type import ChunkerType
from graphrag_chunking.chunker import Chunker
from graphrag_chunking.chunking_config import ChunkingConfig


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


def create_chunker(
    config: ChunkingConfig,
    encode: Callable[[str], list[int]] | None = None,
    decode: Callable[[list[int]], str] | None = None,
) -> Chunker:
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
    if encode is not None:
        config_model["encode"] = encode
    if decode is not None:
        config_model["decode"] = decode
    chunker_strategy = config.type

    if chunker_strategy not in chunker_factory:
        match chunker_strategy:
            case ChunkerType.Tokens:
                from graphrag_chunking.token_chunker import TokenChunker

                register_chunker(ChunkerType.Tokens, TokenChunker)
            case ChunkerType.Sentence:
                from graphrag_chunking.sentence_chunker import SentenceChunker

                register_chunker(ChunkerType.Sentence, SentenceChunker)
            case _:
                msg = f"ChunkingConfig.strategy '{chunker_strategy}' is not registered in the ChunkerFactory. Registered types: {', '.join(chunker_factory.keys())}."
                raise ValueError(msg)

    return chunker_factory.create(chunker_strategy, init_args=config_model)
