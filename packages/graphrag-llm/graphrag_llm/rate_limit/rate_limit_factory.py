# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Rate limit factory."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from graphrag_common.factory import Factory

from graphrag_llm.config import RateLimitType
from graphrag_llm.rate_limit.rate_limiter import RateLimiter

if TYPE_CHECKING:
    from graphrag_common.factory import ServiceScope

    from graphrag_llm.config import RateLimitConfig


class RateLimitFactory(Factory[RateLimiter]):
    """Factory to create RateLimiter instances."""


rate_limit_factory = RateLimitFactory()


def register_rate_limiter(
    rate_limit_type: str,
    rate_limiter_initializer: Callable[..., RateLimiter],
    scope: "ServiceScope" = "transient",
) -> None:
    """Register a custom RateLimiter implementation.

    Args
    ----
        rate_limit_type: str
            The rate limit id to register.
        rate_limiter_initializer: Callable[..., RateLimiter]
            The rate limiter initializer to register.
        scope: ServiceScope (default: "transient")
            The service scope for the rate limiter instance.
    """
    rate_limit_factory.register(
        strategy=rate_limit_type,
        initializer=rate_limiter_initializer,
        scope=scope,
    )


def create_rate_limiter(
    rate_limit_config: "RateLimitConfig",
) -> RateLimiter:
    """Create a RateLimiter instance.

    Args
    ----
        rate_limit_config: RateLimitConfig
            The configuration for the rate limit strategy.

    Returns
    -------
        RateLimiter:
            An instance of a RateLimiter subclass.
    """
    strategy = rate_limit_config.type
    init_args = rate_limit_config.model_dump()

    if strategy not in rate_limit_factory:
        match strategy:
            case RateLimitType.SlidingWindow:
                from graphrag_llm.rate_limit.sliding_window_rate_limiter import (
                    SlidingWindowRateLimiter,
                )

                register_rate_limiter(
                    rate_limit_type=RateLimitType.SlidingWindow,
                    rate_limiter_initializer=SlidingWindowRateLimiter,
                )

            case _:
                msg = f"RateLimitConfig.type '{strategy}' is not registered in the RateLimitFactory. Registered strategies: {', '.join(rate_limit_factory.keys())}"
                raise ValueError(msg)

    return rate_limit_factory.create(strategy=strategy, init_args=init_args)
