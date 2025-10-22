# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tokenizer factory."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from graphrag_common.factory import Factory

from graphrag_llm.config.types import TokenizerType
from graphrag_llm.tokenizer.tokenizer import Tokenizer

if TYPE_CHECKING:
    from graphrag_common.factory import ServiceScope

    from graphrag_llm.config.tokenizer_config import TokenizerConfig


class TokenizerFactory(Factory[Tokenizer]):
    """Factory for creating Tokenizer instances."""


tokenizer_factory = TokenizerFactory()


def register_tokenizer(
    tokenizer_type: str,
    tokenizer_initializer: Callable[..., Tokenizer],
    scope: "ServiceScope" = "transient",
) -> None:
    """Register a custom tokenizer implementation.

    Args
    ----
        tokenizer_type: str
            The tokenizer id to register.
        tokenizer_initializer: Callable[..., Tokenizer]
            The tokenizer initializer to register.
    """
    tokenizer_factory.register(tokenizer_type, tokenizer_initializer, scope)


def create_tokenizer(tokenizer_config: "TokenizerConfig") -> Tokenizer:
    """Create a Tokenizer instance based on the configuration.

    Args
    ----
        tokenizer_config: TokenizerConfig
            The configuration for the tokenizer.

    Returns
    -------
        Tokenizer:
            An instance of a Tokenizer subclass.
    """
    strategy = tokenizer_config.type
    init_args = tokenizer_config.model_dump()

    if strategy not in tokenizer_factory:
        match strategy:
            case TokenizerType.LiteLLM:
                from graphrag_llm.tokenizer.lite_llm_tokenizer import (
                    LiteLLMTokenizer,
                )

                register_tokenizer(
                    TokenizerType.LiteLLM,
                    LiteLLMTokenizer,
                    scope="singleton",
                )
            case TokenizerType.Tiktoken:
                from graphrag_llm.tokenizer.tiktoken_tokenizer import (
                    TiktokenTokenizer,
                )

                register_tokenizer(
                    TokenizerType.Tiktoken,
                    TiktokenTokenizer,
                    scope="singleton",
                )
            case _:
                msg = f"TokenizerConfig.type '{strategy}' is not registered in the TokenizerFactory. Registered strategies: {', '.join(tokenizer_factory.keys())}"
                raise ValueError(msg)

    return tokenizer_factory.create(
        strategy=strategy,
        init_args=init_args,
    )
