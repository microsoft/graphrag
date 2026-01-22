# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Retry factory."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from graphrag_common.factory import Factory

from graphrag_llm.config.types import RetryType
from graphrag_llm.retry.retry import Retry

if TYPE_CHECKING:
    from graphrag_common.factory import ServiceScope

    from graphrag_llm.config.retry_config import RetryConfig


class RetryFactory(Factory[Retry]):
    """Factory to create Retry instances."""


retry_factory = RetryFactory()


def register_retry(
    retry_type: str,
    retry_initializer: Callable[..., Retry],
    scope: "ServiceScope" = "transient",
) -> None:
    """Register a custom Retry implementation.

    Args
    ----
        retry_type: str
            The retry id to register.
        retry_initializer: Callable[..., Retry]
            The retry initializer to register.
    """
    retry_factory.register(
        strategy=retry_type,
        initializer=retry_initializer,
        scope=scope,
    )


def create_retry(
    retry_config: "RetryConfig",
) -> Retry:
    """Create a Retry instance.

    Args
    ----
        retry_config: RetryConfig
            The configuration for the retry strategy.

    Returns
    -------
        Retry:
            An instance of a Retry subclass.
    """
    strategy = retry_config.type
    init_args = retry_config.model_dump()

    if strategy not in retry_factory:
        match strategy:
            case RetryType.ExponentialBackoff:
                from graphrag_llm.retry.exponential_retry import ExponentialRetry

                retry_factory.register(
                    strategy=RetryType.ExponentialBackoff,
                    initializer=ExponentialRetry,
                )
            case RetryType.Immediate:
                from graphrag_llm.retry.immediate_retry import ImmediateRetry

                retry_factory.register(
                    strategy=RetryType.Immediate,
                    initializer=ImmediateRetry,
                )
            case _:
                msg = f"RetryConfig.type '{strategy}' is not registered in the RetryFactory. Registered strategies: {', '.join(retry_factory.keys())}"
                raise ValueError(msg)

    return retry_factory.create(strategy=strategy, init_args=init_args)
