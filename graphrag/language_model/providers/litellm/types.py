# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM types."""

from typing import (
    Any,
    Protocol,
    runtime_checkable,
)

from litellm import (
    AnthropicThinkingParam,
    BaseModel,
    ChatCompletionAudioParam,
    ChatCompletionModality,
    ChatCompletionPredictionContentParam,
    CustomStreamWrapper,
    EmbeddingResponse,  # type: ignore
    ModelResponse,  # type: ignore
    OpenAIWebSearchOptions,
)
from openai.types.chat.chat_completion import (
    ChatCompletion,
    Choice,
)
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, ChoiceDelta
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.completion_usage import (
    CompletionTokensDetails,
    CompletionUsage,
    PromptTokensDetails,
)
from openai.types.create_embedding_response import CreateEmbeddingResponse, Usage
from openai.types.embedding import Embedding

LMChatCompletionMessageParam = ChatCompletionMessageParam | dict[str, str]

LMChatCompletion = ChatCompletion
LMChoice = Choice
LMChatCompletionMessage = ChatCompletionMessage

LMChatCompletionChunk = ChatCompletionChunk
LMChoiceChunk = ChunkChoice
LMChoiceDelta = ChoiceDelta

LMCompletionUsage = CompletionUsage
LMPromptTokensDetails = PromptTokensDetails
LMCompletionTokensDetails = CompletionTokensDetails


LMEmbeddingResponse = CreateEmbeddingResponse
LMEmbedding = Embedding
LMEmbeddingUsage = Usage


@runtime_checkable
class FixedModelCompletion(Protocol):
    """
    Synchronous chat completion function.

    Same signature as litellm.completion but without the `model` parameter
    as this is already set in the model configuration.
    """

    def __call__(
        self,
        *,
        messages: list = [],  # type: ignore  # noqa: B006
        stream: bool | None = None,
        stream_options: dict | None = None,  # type: ignore
        stop=None,  # type: ignore
        max_completion_tokens: int | None = None,
        max_tokens: int | None = None,
        modalities: list[ChatCompletionModality] | None = None,
        prediction: ChatCompletionPredictionContentParam | None = None,
        audio: ChatCompletionAudioParam | None = None,
        logit_bias: dict | None = None,  # type: ignore
        user: str | None = None,
        # openai v1.0+ new params
        response_format: dict | type[BaseModel] | None = None,  # type: ignore
        seed: int | None = None,
        tools: list | None = None,  # type: ignore
        tool_choice: str | dict | None = None,  # type: ignore
        logprobs: bool | None = None,
        top_logprobs: int | None = None,
        parallel_tool_calls: bool | None = None,
        web_search_options: OpenAIWebSearchOptions | None = None,
        deployment_id=None,  # type: ignore
        extra_headers: dict | None = None,  # type: ignore
        # soon to be deprecated params by OpenAI
        functions: list | None = None,  # type: ignore
        function_call: str | None = None,
        # Optional liteLLM function params
        thinking: AnthropicThinkingParam | None = None,
        **kwargs: Any,
    ) -> ModelResponse | CustomStreamWrapper:
        """Chat completion function."""
        ...


@runtime_checkable
class AFixedModelCompletion(Protocol):
    """
    Asynchronous chat completion function.

    Same signature as litellm.acompletion but without the `model` parameter
    as this is already set in the model configuration.
    """

    async def __call__(
        self,
        *,
        # Optional OpenAI params: see https://platform.openai.com/docs/api-reference/chat/create
        messages: list = [],  # type: ignore  # noqa: B006
        stream: bool | None = None,
        stream_options: dict | None = None,  # type: ignore
        stop=None,  # type: ignore
        max_completion_tokens: int | None = None,
        max_tokens: int | None = None,
        modalities: list[ChatCompletionModality] | None = None,
        prediction: ChatCompletionPredictionContentParam | None = None,
        audio: ChatCompletionAudioParam | None = None,
        logit_bias: dict | None = None,  # type: ignore
        user: str | None = None,
        # openai v1.0+ new params
        response_format: dict | type[BaseModel] | None = None,  # type: ignore
        seed: int | None = None,
        tools: list | None = None,  # type: ignore
        tool_choice: str | dict | None = None,  # type: ignore
        logprobs: bool | None = None,
        top_logprobs: int | None = None,
        parallel_tool_calls: bool | None = None,
        web_search_options: OpenAIWebSearchOptions | None = None,
        deployment_id=None,  # type: ignore
        extra_headers: dict | None = None,  # type: ignore
        # soon to be deprecated params by OpenAI
        functions: list | None = None,  # type: ignore
        function_call: str | None = None,
        # Optional liteLLM function params
        thinking: AnthropicThinkingParam | None = None,
        **kwargs: Any,
    ) -> ModelResponse | CustomStreamWrapper:
        """Chat completion function."""
        ...


@runtime_checkable
class FixedModelEmbedding(Protocol):
    """
    Synchronous embedding function.

    Same signature as litellm.embedding but without the `model` parameter
    as this is already set in the model configuration.
    """

    def __call__(
        self,
        *,
        request_id: str | None = None,
        input: list = [],  # type: ignore  # noqa: B006
        # Optional params
        dimensions: int | None = None,
        encoding_format: str | None = None,
        timeout: int = 600,  # default to 10 minutes
        # set api_base, api_version, api_key
        api_base: str | None = None,
        api_version: str | None = None,
        api_key: str | None = None,
        api_type: str | None = None,
        caching: bool = False,
        user: str | None = None,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Embedding function."""
        ...


@runtime_checkable
class AFixedModelEmbedding(Protocol):
    """
    Asynchronous embedding function.

    Same signature as litellm.embedding but without the `model` parameter
    as this is already set in the model configuration.
    """

    async def __call__(
        self,
        *,
        request_id: str | None = None,
        input: list = [],  # type: ignore  # noqa: B006
        # Optional params
        dimensions: int | None = None,
        encoding_format: str | None = None,
        timeout: int = 600,  # default to 10 minutes
        # set api_base, api_version, api_key
        api_base: str | None = None,
        api_version: str | None = None,
        api_key: str | None = None,
        api_type: str | None = None,
        caching: bool = False,
        user: str | None = None,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Embedding function."""
        ...


@runtime_checkable
class LitellmRequestFunc(Protocol):
    """
    Synchronous request function.

    Represents either a chat completion or embedding function.
    """

    def __call__(self, /, **kwargs: Any) -> Any:
        """Request function."""
        ...


@runtime_checkable
class AsyncLitellmRequestFunc(Protocol):
    """
    Asynchronous request function.

    Represents either a chat completion or embedding function.
    """

    async def __call__(self, /, **kwargs: Any) -> Any:
        """Request function."""
        ...
