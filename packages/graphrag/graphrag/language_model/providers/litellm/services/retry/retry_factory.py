# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Retry Factory."""

from graphrag.factory.factory import Factory
from graphrag.language_model.providers.litellm.services.retry.exponential_retry import (
    ExponentialRetry,
)
from graphrag.language_model.providers.litellm.services.retry.incremental_wait_retry import (
    IncrementalWaitRetry,
)
from graphrag.language_model.providers.litellm.services.retry.native_wait_retry import (
    NativeRetry,
)
from graphrag.language_model.providers.litellm.services.retry.random_wait_retry import (
    RandomWaitRetry,
)
from graphrag.language_model.providers.litellm.services.retry.retry import Retry


class RetryFactory(Factory[Retry]):
    """Singleton factory for creating retry services."""


retry_factory = RetryFactory()

retry_factory.register("native", NativeRetry)
retry_factory.register("exponential_backoff", ExponentialRetry)
retry_factory.register("random_wait", RandomWaitRetry)
retry_factory.register("incremental_wait", IncrementalWaitRetry)
