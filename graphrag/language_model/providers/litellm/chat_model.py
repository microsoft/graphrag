# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Chat model implementation using Litellm."""

import inspect
import json
from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING, Any, cast

import litellm
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from litellm import (
    CustomStreamWrapper,
    ModelResponse,  # type: ignore
    acompletion,
    completion,
)
from pydantic import BaseModel, Field

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
    AFixedModelCompletion,
    FixedModelCompletion,
)

if TYPE_CHECKING:
    from graphrag.cache.pipeline_cache import PipelineCache
    from graphrag.config.models.language_model_config import LanguageModelConfig
    from graphrag.language_model.response.base import ModelResponse as MR  # noqa: N817

litellm.suppress_debug_info = True


def _create_base_completions(
    model_config: "LanguageModelConfig",
) -> tuple[FixedModelCompletion, AFixedModelCompletion]:
    """Wrap the base litellm completion function with the model configuration.

    Args
    ----
        model_config: The configuration for the language model.

    Returns
    -------
        A tuple containing the synchronous and asynchronous completion functions.
    """
    model_provider = model_config.model_provider
    model = model_config.deployment_name or model_config.model

    base_args: dict[str, Any] = {
        "drop_params": True,  # LiteLLM drop unsupported params for selected model.
        "model": f"{model_provider}/{model}",
        "timeout": model_config.request_timeout,
        "top_p": model_config.top_p,
        "n": model_config.n,
        "temperature": model_config.temperature,
        "frequency_penalty": model_config.frequency_penalty,
        "presence_penalty": model_config.presence_penalty,
        "api_base": model_config.api_base,
        "api_version": model_config.api_version,
        "api_key": model_config.api_key,
        "organization": model_config.organization,
        "proxy": model_config.proxy,
        "audience": model_config.audience,
        "max_tokens": model_config.max_tokens,
        "max_completion_tokens": model_config.max_completion_tokens,
        "reasoning_effort": model_config.reasoning_effort,
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

    def _base_completion(**kwargs: Any) -> ModelResponse | CustomStreamWrapper:
        new_args = {**base_args, **kwargs}

        if "name" in new_args:
            new_args.pop("name")

        return completion(**new_args)

    async def _base_acompletion(**kwargs: Any) -> ModelResponse | CustomStreamWrapper:
        new_args = {**base_args, **kwargs}

        if "name" in new_args:
            new_args.pop("name")

        return await acompletion(**new_args)

    return (_base_completion, _base_acompletion)


def _create_completions(
    model_config: "LanguageModelConfig",
    cache: "PipelineCache | None",
    cache_key_prefix: str,
) -> tuple[FixedModelCompletion, AFixedModelCompletion]:
    """Wrap the base litellm completion function with the model configuration and additional features.

    Wrap the base litellm completion function with instance variables based on the model configuration.
    Then wrap additional features such as rate limiting, retries, and caching, if enabled.

    Final function composition order:
    - Logging(Cache(Retries(RateLimiter(ModelCompletion()))))

    Args
    ----
        model_config: The configuration for the language model.
        cache: Optional cache for storing responses.
        cache_key_prefix: Prefix for cache keys.

    Returns
    -------
        A tuple containing the synchronous and asynchronous completion functions.

    """
    completion, acompletion = _create_base_completions(model_config)

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
            completion, acompletion = with_rate_limiter(
                sync_fn=completion,
                async_fn=acompletion,
                model_config=model_config,
                rpm=rpm,
                tpm=tpm,
            )

    if model_config.retry_strategy != "none":
        completion, acompletion = with_retries(
            sync_fn=completion,
            async_fn=acompletion,
            model_config=model_config,
        )

    if cache is not None:
        completion, acompletion = with_cache(
            sync_fn=completion,
            async_fn=acompletion,
            model_config=model_config,
            cache=cache,
            request_type="chat",
            cache_key_prefix=cache_key_prefix,
        )

    completion, acompletion = with_logging(
        sync_fn=completion,
        async_fn=acompletion,
    )

    return (completion, acompletion)


class LitellmModelOutput(BaseModel):
    """A model representing the output from a language model."""

    content: str = Field(description="The generated text content")
    full_response: None = Field(
        default=None, description="The full response from the model, if available"
    )


class LitellmModelResponse(BaseModel):
    """A model representing the response from a language model."""

    output: LitellmModelOutput = Field(description="The output from the model")
    parsed_response: BaseModel | None = Field(
        default=None, description="Parsed response from the model"
    )
    history: list = Field(
        default_factory=list,
        description="Conversation history including the prompt and response",
    )


class LitellmChatModel:
    """LiteLLM-based Chat Model."""

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
        self.completion, self.acompletion = _create_completions(
            config, self.cache, "chat"
        )

    def _get_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Get model arguments supported by litellm."""
        args_to_include = [
            "name",
            "modalities",
            "prediction",
            "audio",
            "logit_bias",
            "metadata",
            "user",
            "response_format",
            "seed",
            "tools",
            "tool_choice",
            "logprobs",
            "top_logprobs",
            "parallel_tool_calls",
            "web_search_options",
            "extra_headers",
            "functions",
            "function_call",
            "thinking",
        ]
        new_args = {k: v for k, v in kwargs.items() if k in args_to_include}

        # If using JSON, check if response_format should be a Pydantic model or just a general JSON object
        if kwargs.get("json"):
            new_args["response_format"] = {"type": "json_object"}

            if (
                "json_model" in kwargs
                and inspect.isclass(kwargs["json_model"])
                and issubclass(kwargs["json_model"], BaseModel)
            ):
                new_args["response_format"] = kwargs["json_model"]

        return new_args

    async def achat(
        self, prompt: str, history: list | None = None, **kwargs: Any
    ) -> "MR":
        """
        Generate a response for the given prompt and history.

        Args
        ----
            prompt: The prompt to generate a response for.
            history: Optional chat history.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            LitellmModelResponse: The generated model response.
        """
        new_kwargs = self._get_kwargs(**kwargs)
        messages: list[dict[str, str]] = history or []
        messages.append({"role": "user", "content": prompt})

        response = await self.acompletion(messages=messages, stream=False, **new_kwargs)  # type: ignore

        messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content or "",  # type: ignore
        })

        parsed_response: BaseModel | None = None
        if "response_format" in new_kwargs:
            parsed_dict: dict[str, Any] = json.loads(
                response.choices[0].message.content or "{}"  # type: ignore
            )
            parsed_response = parsed_dict  # type: ignore
            if inspect.isclass(new_kwargs["response_format"]) and issubclass(
                new_kwargs["response_format"], BaseModel
            ):
                # If response_format is a pydantic model, instantiate it
                model_initializer = cast(
                    "type[BaseModel]", new_kwargs["response_format"]
                )
                parsed_response = model_initializer(**parsed_dict)

        return LitellmModelResponse(
            output=LitellmModelOutput(
                content=response.choices[0].message.content or ""  # type: ignore
            ),
            parsed_response=parsed_response,
            history=messages,
        )

    async def achat_stream(
        self, prompt: str, history: list | None = None, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Generate a response for the given prompt and history.

        Args
        ----
            prompt: The prompt to generate a response for.
            history: Optional chat history.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            AsyncGenerator[str, None]: The generated response as a stream of strings.
        """
        new_kwargs = self._get_kwargs(**kwargs)
        messages: list[dict[str, str]] = history or []
        messages.append({"role": "user", "content": prompt})

        response = await self.acompletion(messages=messages, stream=True, **new_kwargs)  # type: ignore

        async for chunk in response:  # type: ignore
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def chat(self, prompt: str, history: list | None = None, **kwargs: Any) -> "MR":
        """
        Generate a response for the given prompt and history.

        Args
        ----
            prompt: The prompt to generate a response for.
            history: Optional chat history.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            LitellmModelResponse: The generated model response.
        """
        new_kwargs = self._get_kwargs(**kwargs)
        messages: list[dict[str, str]] = history or []
        messages.append({"role": "user", "content": prompt})

        response = self.completion(messages=messages, stream=False, **new_kwargs)  # type: ignore

        messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content or "",  # type: ignore
        })

        parsed_response: BaseModel | None = None
        if "response_format" in new_kwargs:
            parsed_dict: dict[str, Any] = json.loads(
                response.choices[0].message.content or "{}"  # type: ignore
            )
            parsed_response = parsed_dict  # type: ignore
            if inspect.isclass(new_kwargs["response_format"]) and issubclass(
                new_kwargs["response_format"], BaseModel
            ):
                # If response_format is a pydantic model, instantiate it
                model_initializer = cast(
                    "type[BaseModel]", new_kwargs["response_format"]
                )
                parsed_response = model_initializer(**parsed_dict)

        return LitellmModelResponse(
            output=LitellmModelOutput(
                content=response.choices[0].message.content or ""  # type: ignore
            ),
            parsed_response=parsed_response,
            history=messages,
        )

    def chat_stream(
        self, prompt: str, history: list | None = None, **kwargs: Any
    ) -> Generator[str, None]:
        """
        Generate a response for the given prompt and history.

        Args
        ----
            prompt: The prompt to generate a response for.
            history: Optional chat history.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            Generator[str, None]: The generated response as a stream of strings.
        """
        new_kwargs = self._get_kwargs(**kwargs)
        messages: list[dict[str, str]] = history or []
        messages.append({"role": "user", "content": prompt})

        response = self.completion(messages=messages, stream=True, **new_kwargs)  # type: ignore

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:  # type: ignore
                yield chunk.choices[0].delta.content  # type: ignore
