# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Create OpenAI client instance."""

import logging
from functools import cache

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI, AsyncOpenAI

from .openai_configuration import OpenAIConfiguration
from .types import OpenAIClientTypes

log = logging.getLogger(__name__)

API_BASE_REQUIRED_FOR_AZURE = "api_base is required for Azure OpenAI client"


@cache
def create_openai_client(
    configuration: OpenAIConfiguration, azure: bool
) -> OpenAIClientTypes:
    """Create a new OpenAI client instance."""
    if azure:
        api_base = configuration.api_base
        if api_base is None:
            raise ValueError(API_BASE_REQUIRED_FOR_AZURE)

        log.info(
            "Creating Azure OpenAI client api_base=%s, deployment_name=%s",
            api_base,
            configuration.deployment_name,
        )
        if configuration.cognitive_services_endpoint is None:
            cognitive_services_endpoint = "https://cognitiveservices.azure.com/.default"
        else:
            cognitive_services_endpoint = configuration.cognitive_services_endpoint

        return AsyncAzureOpenAI(
            api_key=configuration.api_key if configuration.api_key else None,
            azure_ad_token_provider=get_bearer_token_provider(
                DefaultAzureCredential(), cognitive_services_endpoint
            )
            if not configuration.api_key
            else None,
            organization=configuration.organization,
            # Azure-Specifics
            api_version=configuration.api_version,
            azure_endpoint=api_base,
            azure_deployment=configuration.deployment_name,
            # Timeout/Retry Configuration - Use Tenacity for Retries, so disable them here
            timeout=configuration.request_timeout or 180.0,
            max_retries=0,
        )

    log.info("Creating OpenAI client base_url=%s", configuration.api_base)
    return AsyncOpenAI(
        api_key=configuration.api_key,
        base_url=configuration.api_base,
        organization=configuration.organization,
        # Timeout/Retry Configuration - Use Tenacity for Retries, so disable them here
        timeout=configuration.request_timeout or 180.0,
        max_retries=0,
    )
