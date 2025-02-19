# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing utils for fnllm."""

from fnllm.base.config import JsonStrategy, RetryStrategy
from fnllm.openai import AzureOpenAIConfig, OpenAIConfig, PublicOpenAIConfig
from fnllm.openai.types.chat.parameters import OpenAIChatParameters

import graphrag.config.defaults as defs
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.language_model_config import (
    LanguageModelConfig,
)
from graphrag.index.typing import ErrorHandlerFn
from graphrag.language_model.providers.fnllm.cache import FNLLMCacheProvider


def _create_cache(cache: PipelineCache | None, name: str) -> FNLLMCacheProvider | None:
    """Create an FNLLM cache from a pipeline cache."""
    if cache is None:
        return None
    return FNLLMCacheProvider(cache).child(name)


def _create_error_handler(callbacks: WorkflowCallbacks) -> ErrorHandlerFn:
    def on_error(
        error: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        callbacks.error("Error Invoking LLM", error, stack, details)

    return on_error


def _create_openai_config(config: LanguageModelConfig, azure: bool) -> OpenAIConfig:
    encoding_model = config.encoding_model
    json_strategy = (
        JsonStrategy.VALID if config.model_supports_json else JsonStrategy.LOOSE
    )
    chat_parameters = OpenAIChatParameters(
        frequency_penalty=config.frequency_penalty,
        presence_penalty=config.presence_penalty,
        top_p=config.top_p,
        max_tokens=config.max_tokens,
        n=config.n,
        temperature=config.temperature,
    )

    if azure:
        if config.api_base is None:
            msg = "Azure OpenAI Chat LLM requires an API base"
            raise ValueError(msg)

        audience = config.audience or defs.COGNITIVE_SERVICES_AUDIENCE
        return AzureOpenAIConfig(
            api_key=config.api_key,
            endpoint=config.api_base,
            json_strategy=json_strategy,
            api_version=config.api_version,
            organization=config.organization,
            max_retries=config.max_retries,
            max_retry_wait=config.max_retry_wait,
            requests_per_minute=config.requests_per_minute,
            tokens_per_minute=config.tokens_per_minute,
            audience=audience,
            retry_strategy=RetryStrategy(config.retry_strategy),
            timeout=config.request_timeout,
            max_concurrency=config.concurrent_requests,
            model=config.model,
            encoding=encoding_model,
            deployment=config.deployment_name,
            chat_parameters=chat_parameters,
            sleep_on_rate_limit_recommendation=True,
        )
    return PublicOpenAIConfig(
        api_key=config.api_key,
        base_url=config.api_base,
        json_strategy=json_strategy,
        organization=config.organization,
        retry_strategy=RetryStrategy(config.retry_strategy),
        max_retries=config.max_retries,
        max_retry_wait=config.max_retry_wait,
        requests_per_minute=config.requests_per_minute,
        tokens_per_minute=config.tokens_per_minute,
        timeout=config.request_timeout,
        max_concurrency=config.concurrent_requests,
        model=config.model,
        encoding=encoding_model,
        chat_parameters=chat_parameters,
        sleep_on_rate_limit_recommendation=True,
    )
