# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Rate Limiter Factory."""

from graphrag_common.factory import Factory

from graphrag.language_model.providers.litellm.services.rate_limiter.rate_limiter import (
    RateLimiter,
)
from graphrag.language_model.providers.litellm.services.rate_limiter.static_rate_limiter import (
    StaticRateLimiter,
)


class RateLimiterFactory(Factory[RateLimiter]):
    """Singleton factory for creating rate limiter services."""


rate_limiter_factory = RateLimiterFactory()
rate_limiter_factory.register("static", StaticRateLimiter)
