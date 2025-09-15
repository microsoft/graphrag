# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Retry Factory."""

from graphrag.factory.factory import Factory
from graphrag.language_model.providers.litellm.services.retry.retry import Retry


class RetryFactory(Factory[Retry]):
    """Singleton factory for creating retry services."""
