# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for LLM and Embedding models."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from openai import AsyncAzureOpenAI, AsyncOpenAI, AzureOpenAI, OpenAI

from graphrag.query.llm.base import BaseTextEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.progress import ConsoleStatusReporter, StatusReporter


class BaseOpenAILLM(ABC):
    """The Base OpenAI LLM implementation."""

    _async_client: AsyncOpenAI | AsyncAzureOpenAI
    _sync_client: OpenAI | AzureOpenAI

    def __init__(self):
        self._create_openai_client()

    @abstractmethod
    def _create_openai_client(self):
        """Create a new synchronous and asynchronous OpenAI client instance."""

    def set_clients(
        self,
        sync_client: OpenAI | AzureOpenAI,
        async_client: AsyncOpenAI | AsyncAzureOpenAI,
    ):
        """
        Set the synchronous and asynchronous clients used for making API requests.

        Args:
            sync_client (OpenAI | AzureOpenAI): The sync client object.
            async_client (AsyncOpenAI | AsyncAzureOpenAI): The async client object.
        """
        self._sync_client = sync_client
        self._async_client = async_client

    @property
    def async_client(self) -> AsyncOpenAI | AsyncAzureOpenAI | None:
        """
        Get the asynchronous client used for making API requests.

        Returns
        -------
            AsyncOpenAI | AsyncAzureOpenAI: The async client object.
        """
        return self._async_client

    @property
    def sync_client(self) -> OpenAI | AzureOpenAI | None:
        """
        Get the synchronous client used for making API requests.

        Returns
        -------
            AsyncOpenAI | AsyncAzureOpenAI: The async client object.
        """
        return self._sync_client

    @async_client.setter
    def async_client(self, client: AsyncOpenAI | AsyncAzureOpenAI):
        """
        Set the asynchronous client used for making API requests.

        Args:
            client (AsyncOpenAI | AsyncAzureOpenAI): The async client object.
        """
        self._async_client = client

    @sync_client.setter
    def sync_client(self, client: OpenAI | AzureOpenAI):
        """
        Set the synchronous client used for making API requests.

        Args:
            client (OpenAI | AzureOpenAI): The sync client object.
        """
        self._sync_client = client


class OpenAILLMImpl(BaseOpenAILLM):
    """Orchestration OpenAI LLM Implementation."""

    _reporter: StatusReporter = ConsoleStatusReporter()

    def __init__(
        self,
        api_key: str | None = None,
        azure_ad_token_provider: Callable | None = None,
        deployment_name: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        api_type: OpenaiApiType = OpenaiApiType.OpenAI,
        organization: str | None = None,
        max_retries: int = 10,
        request_timeout: float = 180.0,
        reporter: StatusReporter | None = None,
    ):
        self.api_key = api_key
        self.azure_ad_token_provider = azure_ad_token_provider
        self.deployment_name = deployment_name
        self.api_base = api_base
        self.api_version = api_version
        self.api_type = api_type
        self.organization = organization
        self.max_retries = max_retries
        self.request_timeout = request_timeout
        self.reporter = reporter or ConsoleStatusReporter()

        try:
            # Create OpenAI sync and async clients
            super().__init__()
        except Exception as e:
            self._reporter.error(
                message="Failed to create OpenAI client",
                details={self.__class__.__name__: str(e)},
            )
            raise

    def _create_openai_client(self):
        """Create a new OpenAI client instance."""
        if self.api_type == OpenaiApiType.AzureOpenAI:
            if self.api_base is None:
                msg = "api_base is required for Azure OpenAI"
                raise ValueError(msg)

            sync_client = AzureOpenAI(
                api_key=self.api_key,
                azure_ad_token_provider=self.azure_ad_token_provider,
                organization=self.organization,
                # Azure-Specifics
                api_version=self.api_version,
                azure_endpoint=self.api_base,
                azure_deployment=self.deployment_name,
                # Retry Configuration
                timeout=self.request_timeout,
                max_retries=self.max_retries,
            )

            async_client = AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_ad_token_provider=self.azure_ad_token_provider,
                organization=self.organization,
                # Azure-Specifics
                api_version=self.api_version,
                azure_endpoint=self.api_base,
                azure_deployment=self.deployment_name,
                # Retry Configuration
                timeout=self.request_timeout,
                max_retries=self.max_retries,
            )
            self.set_clients(sync_client=sync_client, async_client=async_client)

        else:
            sync_client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                organization=self.organization,
                # Retry Configuration
                timeout=self.request_timeout,
                max_retries=self.max_retries,
            )

            async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                organization=self.organization,
                # Retry Configuration
                timeout=self.request_timeout,
                max_retries=self.max_retries,
            )
            self.set_clients(sync_client=sync_client, async_client=async_client)


class OpenAITextEmbeddingImpl(BaseTextEmbedding):
    """Orchestration OpenAI Text Embedding Implementation."""

    _reporter: StatusReporter | None = None

    def _create_openai_client(self, api_type: OpenaiApiType):
        """Create a new synchronous and asynchronous OpenAI client instance."""
