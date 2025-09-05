# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Retry Factory."""

from typing import Any, ClassVar

from graphrag.language_model.providers.litellm.services.retry.exponential_retry import (
    ExponentialRetry,
)
from graphrag.language_model.providers.litellm.services.retry.incremental_wait_retry import (
    IncrementalWaitRetry,
)
from graphrag.language_model.providers.litellm.services.retry.native_retry import (
    NativeRetry,
)
from graphrag.language_model.providers.litellm.services.retry.random_wait_retry import (
    RandomWaitRetry,
)
from graphrag.language_model.providers.litellm.services.retry.retry import Retry

# Same retry strategies fnllm supports.
DEFAULT_RETRY_SERVICES: dict[str, type[Retry]] = {
    "native": NativeRetry,
    "exponential_backoff": ExponentialRetry,
    "random_wait": RandomWaitRetry,
    "incremental_wait": IncrementalWaitRetry,
}


class RetryFactory:
    """Singleton factory for creating retry services."""

    _instance: ClassVar["RetryFactory | None"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "RetryFactory":
        """Create a new instance of RetryFactory if it does not exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._retry_services: dict[str, type[Retry]] = DEFAULT_RETRY_SERVICES
            self._initialized = True

    def register_retry_service(
        self, *, strategy: str, retry_class: type[Retry]
    ) -> None:
        """
        Register a new retry service.

        Args
        ----
            strategy: The name of the retry strategy.
            retry_class: The class implementing the retry strategy.
        """
        self._retry_services[strategy] = retry_class

    def create_retry_service(self, *, strategy: str, **kwargs: Any) -> Retry:
        """
        Create a retry service.

        Args
        ----
            strategy: The name of the retry strategy to use.
            **kwargs: Additional keyword arguments to pass to the retry service constructor.

        Strategies
        ----------
            - native: Retry immediately, works well when paired with rate limiting as rate limiter
                will throttle retries. This is the default retry strategy created by graphrag init.
            - exponential_backoff: Uses exponential backoff for retries.
            - random_wait: Uses random wait times between retries.
            - incremental_wait: Uses incremental wait times between retries.

        Returns
        -------
            Retry: An instance of the specified retry service.
        """
        if strategy not in self._retry_services:
            msg = f"Unknown retry strategy: {strategy}"
            raise ValueError(msg)

        retry_class = self._retry_services[strategy]
        return retry_class(**kwargs)
