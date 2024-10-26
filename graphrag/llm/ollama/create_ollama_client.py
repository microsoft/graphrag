# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Create OpenAI client instance."""

import logging
from functools import cache

from ollama import AsyncClient, Client

from .ollama_configuration import OllamaConfiguration
from .types import OllamaClientType

log = logging.getLogger(__name__)

API_BASE_REQUIRED_FOR_AZURE = "api_base is required for Azure OpenAI client"


@cache
def create_ollama_client(
    configuration: OllamaConfiguration,
    sync: bool = False,
) -> OllamaClientType:
    """Create a new Ollama client instance."""

    log.info("Creating OpenAI client base_url=%s", configuration.api_base)
    if sync:
        return Client(
            host=configuration.api_base,
            timeout=configuration.request_timeout or 180.0,
        )
    return AsyncClient(
        host=configuration.api_base,
        # Timeout/Retry Configuration - Use Tenacity for Retries, so disable them here
        timeout=configuration.request_timeout or 180.0,
    )
