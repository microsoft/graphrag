# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Rate Limiter Factory."""

from graphrag.config.defaults import DEFAULT_RATE_LIMITER_SERVICES
from graphrag.factory.factory import Factory
from graphrag.language_model.providers.litellm.services.rate_limiter.rate_limiter import (
    RateLimiter,
)


class RateLimiterFactory(Factory[RateLimiter]):
    """Singleton factory for creating rate limiter services."""


rate_limiter_factory = RateLimiterFactory()

for service_name, service_cls in DEFAULT_RATE_LIMITER_SERVICES.items():
    rate_limiter_factory.register(
        strategy=service_name, service_initializer=service_cls
    )
