# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Types for graphrag-llm."""

from collections.abc import AsyncIterator, Awaitable, Iterator, Sequence
from typing import (
    Any,
    Generic,
    Literal,
    Protocol,
    Required,
    TypeVar,
    Unpack,
    runtime_checkable,
)

from litellm import (
    AnthropicThinkingParam,
    ChatCompletionAudioParam,
    ChatCompletionModality,
    ChatCompletionPredictionContentParam,
    OpenAIWebSearchOptions,
)
from openai.types.chat.chat_completion import (
    ChatCompletion,
    Choice,
)
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, ChoiceDelta
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_function_tool_param import (
    ChatCompletionFunctionToolParam,
)
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.completion_usage import (
    CompletionTokensDetails,
    CompletionUsage,
    PromptTokensDetails,
)
from openai.types.create_embedding_response import CreateEmbeddingResponse, Usage
from openai.types.embedding import Embedding
from pydantic import BaseModel, computed_field
from typing_extensions import TypedDict

LLMCompletionMessagesParam = str | Sequence[ChatCompletionMessageParam | dict[str, Any]]

LLMChoice = Choice
LLMCompletionMessage = ChatCompletionMessage

LLMCompletionChunk = ChatCompletionChunk
LLMChoiceChunk = ChunkChoice
LLMChoiceDelta = ChoiceDelta

LLMCompletionUsage = CompletionUsage
LLMPromptTokensDetails = PromptTokensDetails
LLMCompletionTokensDetails = CompletionTokensDetails


LLMEmbedding = Embedding
LLMEmbeddingUsage = Usage

LLMCompletionFunctionToolParam = ChatCompletionFunctionToolParam


Metrics = dict[str, float]
"""Represents single request metrics and aggregated metrics for an entire model.

example: {
    "duration_ms": 123.45,
    "successful_requests": 1,
}

On the individual request level, successful_requests will be either 0 or 1.
On the aggregated model level, successful_requests will be the sum of all
successful requests.
"""

ResponseFormat = TypeVar(
    "ResponseFormat",
    bound=BaseModel,
)
"""Generic type variable for structured response format."""


class LLMCompletionResponse(ChatCompletion, Generic[ResponseFormat]):
    """LLM Completion Response extending OpenAI ChatCompletion.

    The response type returned by graphrag-llm LLMCompletionFunction.
    graphrag-llm automatically handles structured response parsing based on the
    provided ResponseFormat model.
    """

    formatted_response: ResponseFormat | None = None  # type: ignore
    """Formatted response according to the specified response_format json schema."""

    @computed_field
    @property
    def content(self) -> str:
        """Get the content of the first choice message."""
        return self.choices[0].message.content or ""


class LLMCompletionArgs(
    TypedDict, Generic[ResponseFormat], total=False, extra_items=Any
):
    """Arguments for LLMCompletionFunction.

    Same signature as litellm.completion but without the `model` parameter
    as this is already set in the model configuration.
    """

    messages: Required[LLMCompletionMessagesParam]
    response_format: type[ResponseFormat] | None
    timeout: float | None
    temperature: float | None
    top_p: float | None
    n: int | None
    stream: bool | None
    stream_options: dict | None
    stop: None
    max_completion_tokens: int | None
    max_tokens: int | None
    modalities: list[ChatCompletionModality] | None
    prediction: ChatCompletionPredictionContentParam | None
    audio: ChatCompletionAudioParam | None
    presence_penalty: float | None
    frequency_penalty: float | None
    logit_bias: dict | None
    user: str | None
    reasoning_effort: (
        Literal["none", "minimal", "low", "medium", "high", "default"] | None
    )
    seed: int | None
    tools: list | None
    tool_choice: str | dict | None
    logprobs: bool | None
    top_logprobs: int | None
    parallel_tool_calls: bool | None
    web_search_options: OpenAIWebSearchOptions | None
    deployment_id: Any
    extra_headers: dict | None
    safety_identifier: str | None
    functions: list | None
    function_call: str | None
    thinking: AnthropicThinkingParam | None


@runtime_checkable
class LLMCompletionFunction(Protocol):
    """Synchronous completion function.

    Same signature as litellm.completion but without the `model` parameter
    as this is already set in the model configuration.
    """

    def __call__(
        self, /, **kwargs: Unpack[LLMCompletionArgs[ResponseFormat]]
    ) -> LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk]:
        """Completion function."""
        ...


@runtime_checkable
class AsyncLLMCompletionFunction(Protocol):
    """Asynchronous completion function.

    Same signature as litellm.completion but without the `model` parameter
    as this is already set in the model configuration.
    """

    def __call__(
        self, /, **kwargs: Unpack[LLMCompletionArgs[ResponseFormat]]
    ) -> Awaitable[
        LLMCompletionResponse[ResponseFormat] | AsyncIterator[LLMCompletionChunk]
    ]:
        """Completion function."""
        ...


class LLMEmbeddingResponse(CreateEmbeddingResponse):
    """LLM Embedding Response extending OpenAI CreateEmbeddingResponse.

    The response type returned by graphrag-llm LLMEmbeddingFunction.
    Adds utilities for accessing embeddings.
    """

    @computed_field
    @property
    def embeddings(self) -> list[list[float]]:
        """Get the embeddings as a list of lists of floats."""
        return [data.embedding for data in self.data]

    @computed_field
    @property
    def first_embedding(self) -> list[float]:
        """Get the first embedding."""
        return self.embeddings[0] if self.embeddings else []


class LLMEmbeddingArgs(TypedDict, total=False, extra_items=Any):
    """Arguments for embedding functions.

    Same signature as litellm.embedding but without the `model` parameter
    as this is already set in the model configuration.
    """

    input: Required[list[str]]
    dimensions: int | None
    encoding_format: str | None
    timeout: int
    user: str | None


@runtime_checkable
class LLMEmbeddingFunction(Protocol):
    """Synchronous embedding function.

    Same signature as litellm.embedding but without the `model` parameter
    as this is already set in the model configuration.
    """

    def __call__(
        self,
        /,
        **kwargs: Unpack[LLMEmbeddingArgs],
    ) -> LLMEmbeddingResponse:
        """Embedding function."""
        ...


@runtime_checkable
class AsyncLLMEmbeddingFunction(Protocol):
    """Asynchronous embedding function.

    Same signature as litellm.aembedding but without the `model` parameter
    as this is already set in the model configuration.
    """

    async def __call__(
        self,
        /,
        **kwargs: Unpack[LLMEmbeddingArgs],
    ) -> LLMEmbeddingResponse:
        """Embedding function."""
        ...


LLMFunction = TypeVar("LLMFunction", LLMCompletionFunction, LLMEmbeddingFunction)
"""Generic representation of completion and embedding functions.

This type is used in the middleware pipeline as the pipeline can handle both
completion and embedding functions. That way services such as retries, caching,
and rate limiting can be reused for both completions and embeddings.
"""

AsyncLLMFunction = TypeVar(
    "AsyncLLMFunction", AsyncLLMCompletionFunction, AsyncLLMEmbeddingFunction
)
"""Generic representation of asynchronous completion and embedding functions.

This type is used in the middleware pipeline as the pipeline can handle both
completion and embedding functions. That way services such as retries, caching,
and rate limiting can be reused for both completions and embeddings.
"""
