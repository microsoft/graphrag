# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Create OpenAI client instance."""

import os
import logging
from functools import cache

from azure.identity import ManagedIdentityCredential, get_bearer_token_provider, DefaultAzureCredential, InteractiveBrowserCredential
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
        
        azure_credentials = DefaultAzureCredential(managed_identity_client_id=os.getenv('AZURE_CLIENT_ID'), exclude_interactive_browser_credential = False)
        token_provider = get_bearer_token_provider(azure_credentials, cognitive_services_endpoint)
        
        return AsyncAzureOpenAI(
            azure_ad_token_provider=token_provider,
            api_version=configuration.api_version,
            azure_endpoint=api_base,
            azure_deployment=configuration.deployment_name
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
