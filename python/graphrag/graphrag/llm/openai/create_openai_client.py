# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Create OpenAI client instance."""

from functools import cache

from openai import AsyncAzureOpenAI, AsyncOpenAI

from .openai_configuration import OpenAIConfiguration
from .types import OpenAIClientTypes


@cache
def create_openai_client(
    configuration: OpenAIConfiguration, azure: bool
) -> OpenAIClientTypes:
    """Create a new OpenAI client instance."""
    if azure:
        api_base = configuration.api_base
        if api_base is None:
            raise ValueError

        return AsyncAzureOpenAI(
            api_key=configuration.api_key,
            organization=configuration.organization,
            # Azure-Specifics
            api_version=configuration.api_version,
            azure_endpoint=api_base,
            azure_deployment=configuration.deployment_name,
            # Timeout/Retry Configuration - Use Tenacity for Retries, so disable them here
            timeout=configuration.request_timeout or 180.0,
            max_retries=0,
        )
    return AsyncOpenAI(
        api_key=configuration.api_key,
        base_url=configuration.api_base,
        organization=configuration.organization,
        # Timeout/Retry Configuration - Use Tenacity for Retries, so disable them here
        timeout=configuration.request_timeout or 180.0,
        max_retries=0,
    )
