# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Embedding model implementation using Litellm."""

from typing import TYPE_CHECKING, Any

import litellm
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from litellm import (
    EmbeddingResponse,  # type: ignore
    aembedding,
    embedding,
)

from graphrag.config.defaults import COGNITIVE_SERVICES_AUDIENCE
from graphrag.config.enums import AuthType
from graphrag.language_model.providers.litellm.request_wrappers.with_cache import (
    with_cache,
)
from graphrag.language_model.providers.litellm.request_wrappers.with_logging import (
    with_logging,
)
from graphrag.language_model.providers.litellm.request_wrappers.with_rate_limiter import (
    with_rate_limiter,
)
from graphrag.language_model.providers.litellm.request_wrappers.with_retries import (
    with_retries,
)
from graphrag.language_model.providers.litellm.types import (
    AFixedModelEmbedding,
    FixedModelEmbedding,
)

if TYPE_CHECKING:
    from graphrag.cache.pipeline_cache import PipelineCache
    from graphrag.config.models.language_model_config import LanguageModelConfig

litellm.suppress_debug_info = True


def _create_base_embeddings(
    model_config: "LanguageModelConfig",
) -> tuple[FixedModelEmbedding, AFixedModelEmbedding]:
    """Wrap the base litellm embedding function with the model configuration.

    Args
    ----
        model_config: The configuration for the language model.

    Returns
    -------
        A tuple containing the synchronous and asynchronous embedding functions.
    """
    model_provider = model_config.model_provider
    model = model_config.deployment_name or model_config.model

    base_args: dict[str, Any] = {
        "drop_params": True,  # LiteLLM drop unsupported params for selected model.
        "model": f"{model_provider}/{model}",
        "timeout": model_config.request_timeout,
        "api_base": model_config.api_base,
        "api_version": model_config.api_version,
        "api_key": model_config.api_key,
        "organization": model_config.organization,
        "proxy": model_config.proxy,
        "audience": model_config.audience,
    }

    if model_config.auth_type == AuthType.AzureManagedIdentity:
        if model_config.model_provider != "azure":
            msg = "Azure Managed Identity authentication is only supported for Azure models."
            raise ValueError(msg)

        base_args["azure_scope"] = base_args.pop("audience")
        base_args["azure_ad_token_provider"] = get_bearer_token_provider(
            DefaultAzureCredential(),
            model_config.audience or COGNITIVE_SERVICES_AUDIENCE,
        )

    def _base_embedding(**kwargs: Any) -> EmbeddingResponse:
        new_args = {**base_args, **kwargs}

        if "name" in new_args:
            new_args.pop("name")

        return embedding(**new_args)

    async def _base_aembedding(**kwargs: Any) -> EmbeddingResponse:
        new_args = {**base_args, **kwargs}

        if "name" in new_args:
            new_args.pop("name")

        return await aembedding(**new_args)

    return (_base_embedding, _base_aembedding)


def _create_embeddings(
    model_config: "LanguageModelConfig",
    cache: "PipelineCache | None",
    cache_key_prefix: str,
) -> tuple[FixedModelEmbedding, AFixedModelEmbedding]:
    """Wrap the base litellm embedding function with the model configuration and additional features.

    Wrap the base litellm embedding function with instance variables based on the model configuration.
    Then wrap additional features such as rate limiting, retries, and caching, if enabled.

    Final function composition order:
    - Logging(Cache(Retries(RateLimiter(ModelEmbedding()))))

    Args
    ----
        model_config: The configuration for the language model.
        cache: Optional cache for storing responses.
        cache_key_prefix: Prefix for cache keys.

    Returns
    -------
        A tuple containing the synchronous and asynchronous embedding functions.

    """
    embedding, aembedding = _create_base_embeddings(model_config)

    # TODO: For v2.x release, rpm/tpm can be int or str (auto) for backwards compatibility with fnllm.
    # LiteLLM does not support "auto", so we have to check those values here.
    # For v3 release, force rpm/tpm to be int and remove the type checks below
    # and just check if rate_limit_strategy is enabled.
    if model_config.rate_limit_strategy is not None:
        rpm = (
            model_config.requests_per_minute
            if type(model_config.requests_per_minute) is int
            else None
        )
        tpm = (
            model_config.tokens_per_minute
            if type(model_config.tokens_per_minute) is int
            else None
        )
        if rpm is not None or tpm is not None:
            embedding, aembedding = with_rate_limiter(
                sync_fn=embedding,
                async_fn=aembedding,
                model_config=model_config,
                rpm=rpm,
                tpm=tpm,
            )

    if model_config.retry_strategy != "none":
        embedding, aembedding = with_retries(
            sync_fn=embedding,
            async_fn=aembedding,
            model_config=model_config,
        )

    if cache is not None:
        embedding, aembedding = with_cache(
            sync_fn=embedding,
            async_fn=aembedding,
            model_config=model_config,
            cache=cache,
            request_type="embedding",
            cache_key_prefix=cache_key_prefix,
        )

    embedding, aembedding = with_logging(
        sync_fn=embedding,
        async_fn=aembedding,
    )

    return (embedding, aembedding)


class LitellmEmbeddingModel:
    """LiteLLM-based Embedding Model."""

    def __init__(
        self,
        name: str,
        config: "LanguageModelConfig",
        cache: "PipelineCache | None" = None,
        **kwargs: Any,
    ):
        self.name = name
        self.config = config
        self.cache = cache.child(self.name) if cache else None
        self.embedding, self.aembedding = _create_embeddings(
            config, self.cache, "embeddings"
        )

    def _get_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Get model arguments supported by litellm."""
        args_to_include = [
            "name",
            "dimensions",
            "encoding_format",
            "timeout",
            "user",
        ]
        return {k: v for k, v in kwargs.items() if k in args_to_include}

    async def aembed_batch(
        self, text_list: list[str], **kwargs: Any
    ) -> list[list[float]]:
        """
        Batch generate embeddings.

        Args
        ----
            text_list: A batch of text inputs to generate embeddings for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A Batch of embeddings.
        """
        new_kwargs = self._get_kwargs(**kwargs)
        response = await self.aembedding(input=text_list, **new_kwargs)

        return [emb.get("embedding", []) for emb in response.data]

    async def aembed(self, text: str, **kwargs: Any) -> list[float]:
        """
        Async embed.

        Args:
            text: The text to generate an embedding for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            An embedding.
        """
        new_kwargs = self._get_kwargs(**kwargs)
        response = await self.aembedding(input=[text], **new_kwargs)

        return (
            response.data[0].get("embedding", [])
            if response.data and response.data[0]
            else []
        )

    def embed_batch(self, text_list: list[str], **kwargs: Any) -> list[list[float]]:
        """
        Batch generate embeddings.

        Args:
            text_list: A batch of text inputs to generate embeddings for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A Batch of embeddings.
        """
        new_kwargs = self._get_kwargs(**kwargs)
        response = self.embedding(input=text_list, **new_kwargs)

        return [emb.get("embedding", []) for emb in response.data]

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """
        Embed a single text input.

        Args:
            text: The text to generate an embedding for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            An embedding.
        """
        new_kwargs = self._get_kwargs(**kwargs)
        response = self.embedding(input=[text], **new_kwargs)

        return (
            response.data[0].get("embedding", [])
            if response.data and response.data[0]
            else []
        )
