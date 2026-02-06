# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Completion Abstract Base Class."""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Unpack

from graphrag_llm.threading.completion_thread_runner import completion_thread_runner

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from graphrag_cache import Cache, CacheKeyCreator

    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsProcessor, MetricsStore
    from graphrag_llm.rate_limit import RateLimiter
    from graphrag_llm.retry import Retry
    from graphrag_llm.threading.completion_thread_runner import (
        ThreadedLLMCompletionFunction,
        ThreadedLLMCompletionResponseHandler,
    )
    from graphrag_llm.tokenizer import Tokenizer
    from graphrag_llm.types import (
        LLMCompletionArgs,
        LLMCompletionChunk,
        LLMCompletionResponse,
        ResponseFormat,
    )


class LLMCompletion(ABC):
    """Abstract base class for language model completions."""

    @abstractmethod
    def __init__(
        self,
        *,
        model_id: str,
        model_config: "ModelConfig",
        tokenizer: "Tokenizer",
        metrics_store: "MetricsStore",
        metrics_processor: "MetricsProcessor | None" = None,
        rate_limiter: "RateLimiter | None" = None,
        retrier: "Retry | None" = None,
        cache: "Cache | None" = None,
        cache_key_creator: "CacheKeyCreator",
        **kwargs: Any,
    ):
        """Initialize the LLMCompletion.

        Args
        ----
            model_id: str
                The model ID, e.g., "openai/gpt-4o".
            model_config: ModelConfig
                The configuration for the language model.
            tokenizer: Tokenizer
                The tokenizer to use.
            metrics_store: MetricsStore | None (default=None)
                The metrics store to use.
            metrics_processor: MetricsProcessor | None (default: None)
                The metrics processor to use.
            rate_limiter: RateLimiter | None (default=None)
                The rate limiter to use.
            retrier: Retry | None (default=None)
                The retry strategy to use.
            cache: Cache | None (default=None)
                Optional cache for embeddings.
            cache_key_creator: CacheKeyCreator | None (default=None)
                Optional cache key creator function.
                (dict[str, Any]) -> str
            **kwargs: Any
                Additional keyword arguments.
        """
        raise NotImplementedError

    @abstractmethod
    def completion(
        self,
        /,
        **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"],
    ) -> "LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk]":
        """Sync completion method.

        Args
        ----
            messages: LLMCompletionMessagesParam
                The messages to send to the LLM.
                Can be str | list[dict[str, str]] | list[ChatCompletionMessageParam].
            response_format: BaseModel | None (default=None)
                The structured response format.
                Must extend pydantic BaseModel.
            stream: bool (default=False)
                Whether to stream the response.
                streaming is not supported when using response_format.
            max_completion_tokens: int | None (default=None)
                The maximum number of tokens to generate in the completion.
            temperature: float | None (default=None)
                The temperature to control how deterministic vs. creative the responses are.
            top_p: float | None (default=None)
                 top_p for nucleus sampling, where the model considers tokens with
                 cumulative probabilities up to top_p. Values range from 0 to 1.
            n: int | None (default=None)
                The number of completions to generate for each prompt.
            tools: list[Tool] | None (default=None)
                Optional tools to use during completion.
                https://docs.litellm.ai/docs/completion/function_call
            **kwargs: Any
                Additional keyword arguments.

        Returns
        -------
            LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk]:
                The completion response or an iterator of completion chunks if streaming.

        """
        raise NotImplementedError

    @abstractmethod
    async def completion_async(
        self,
        /,
        **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"],
    ) -> "LLMCompletionResponse[ResponseFormat] | AsyncIterator[LLMCompletionChunk]":
        """Async completion method.

        Args
        ----
            messages: LLMCompletionMessagesParam
                The messages to send to the LLM.
                Can be str | list[dict[str, str]] | list[ChatCompletionMessageParam].
            response_format: BaseModel | None (default=None)
                The structured response format.
                Must extend pydantic BaseModel.
            stream: bool (default=False)
                Whether to stream the response.
                streaming is not supported when using response_format.
            max_completion_tokens: int | None (default=None)
                The maximum number of tokens to generate in the completion.
            temperature: float | None (default=None)
                The temperature to control how deterministic vs. creative the responses are.
            top_p: float | None (default=None)
                 top_p for nucleus sampling, where the model considers tokens with
                 cumulative probabilities up to top_p. Values range from 0 to 1.
            n: int | None (default=None)
                The number of completions to generate for each prompt.
            tools: list[Tool] | None (default=None)
                Optional tools to use during completion.
                https://docs.litellm.ai/docs/completion/function_call
            **kwargs: Any
                Additional keyword arguments.

        Returns
        -------
            LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk]:
                The completion response or an iterator of completion chunks if streaming.
        """
        raise NotImplementedError

    @contextmanager
    def completion_thread_pool(
        self,
        *,
        response_handler: "ThreadedLLMCompletionResponseHandler",
        concurrency: int,
        queue_limit: int = 0,
    ) -> "Iterator[ThreadedLLMCompletionFunction]":
        """Run a completion thread pool.

        Args
        ----
            response_handler: ThreadedLLMCompletionResponseHandler
                The callback function to handle completion responses.
                (request_id, response|exception) -> Awaitable[None] | None
            concurrency: int
                The number of threads to spin up in a thread pool.
            queue_limit: int (default=0)
                The maximum number of items allowed in the input queue.
                0 means unlimited.
                Set this to a value to create backpressure on the caller.

        Yields
        ------
            ThreadedLLMCompletionFunction:
                A function that can be used to submit completion requests to the thread pool.
                (messages, request_id, **kwargs) -> None

                The thread pool will process the requests and invoke the provided callback
                with the responses.

                same signature as LLMCompletionFunction but requires a `request_id` parameter
                to identify the request and does not return anything.
        """
        with completion_thread_runner(
            completion=self.completion,
            response_handler=response_handler,
            concurrency=concurrency,
            queue_limit=queue_limit,
            metrics_store=self.metrics_store,
        ) as completion:
            yield completion

    def completion_batch(
        self,
        completion_requests: list["LLMCompletionArgs[ResponseFormat]"],
        *,
        concurrency: int,
        queue_limit: int = 0,
    ) -> list[
        "LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk] | Exception"
    ]:
        """Process a batch of completion requests using a thread pool.

        Args
        ----
            completion_requests: list[LLMCompletionArgs]
                A list of completion request arguments to process in parallel.
            concurrency: int
                The number of threads to spin up in a thread pool.
            queue_limit: int (default=0)
                The maximum number of items allowed in the input queue.
                0 means unlimited.
                Set this to a value to create backpressure on the caller.

        Returns
        -------
            list[LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk] | Exception]:
                A list of completion responses or exceptions corresponding to all the requests.
        """
        responses: list[
            LLMCompletionResponse[ResponseFormat]
            | Iterator[LLMCompletionChunk]
            | Exception
        ] = [None] * len(completion_requests)  # type: ignore

        def handle_response(
            request_id: str,
            resp: "LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk] | Exception",
        ):
            responses[int(request_id)] = resp

        with self.completion_thread_pool(
            response_handler=handle_response,
            concurrency=concurrency,
            queue_limit=queue_limit,
        ) as threaded_completion:
            for idx, request in enumerate(completion_requests):
                threaded_completion(request_id=str(idx), **request)

        return responses

    @property
    @abstractmethod
    def metrics_store(self) -> "MetricsStore":
        """Metrics store."""
        raise NotImplementedError

    @property
    @abstractmethod
    def tokenizer(self) -> "Tokenizer":
        """Tokenizer."""
        raise NotImplementedError
