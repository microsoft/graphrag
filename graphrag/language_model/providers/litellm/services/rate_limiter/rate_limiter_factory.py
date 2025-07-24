# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Rate Limiter Factory."""

from typing import Any, ClassVar

from graphrag.language_model.providers.litellm.services.rate_limiter.rate_limiter import (
    RateLimiter,
)
from graphrag.language_model.providers.litellm.services.rate_limiter.static_rate_limiter import (
    StaticRateLimiter,
)

DEFAULT_RATE_LIMITER_SERVICES: dict[str, type[RateLimiter]] = {
    "static": StaticRateLimiter,
}


class RateLimiterFactory:
    """Singleton factory for creating rate limiter services."""

    _instance: ClassVar["RateLimiterFactory | None"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "RateLimiterFactory":
        """Create a new instance of RateLimiterFactory if it does not exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the RateLimiterFactory with default rate limiters."""
        if not hasattr(self, "_initialized"):
            self._rate_limiter_services: dict[str, type[RateLimiter]] = (
                DEFAULT_RATE_LIMITER_SERVICES
            )
            self._initialized = True

    def register_rate_limiter_service(
        self, *, strategy: str, rate_limiter_class: type[RateLimiter]
    ) -> None:
        """
        Register a new rate limiter service.

        Args
        ----
            strategy: The name of the rate limiter strategy.
            rate_limiter_class: The class implementing the rate limiter strategy.
        """
        self._rate_limiter_services[strategy] = rate_limiter_class

    def create_rate_limiter_service(
        self, *, strategy: str, **kwargs: Any
    ) -> RateLimiter:
        """
        Create a rate limiter service.

        Args
        ----
            strategy: The name of the rate limiter strategy.
            **kwargs: Additional keyword arguments to pass to the rate limiter's constructor.

        Returns
        -------
            An instance of the specified rate limiter service.
        """
        if strategy not in self._rate_limiter_services:
            msg = f"Unknown rate limiter service: {strategy}"
            raise ValueError(msg)

        rate_limiter_initializer = self._rate_limiter_services[strategy]
        return rate_limiter_initializer(**kwargs)
