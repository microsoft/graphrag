# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Rate Limiter Factory."""

from graphrag.factory.factory import Factory
from graphrag.language_model.providers.litellm.services.rate_limiter.rate_limiter import (
    RateLimiter,
)


class RateLimiterFactory(Factory[RateLimiter]):
    """Singleton factory for creating rate limiter services."""
