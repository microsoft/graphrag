# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Completion Abstract Base Class."""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Unpack

from graphrag_llm.threading.embedding_thread_runner import embedding_thread_runner

if TYPE_CHECKING:
    from collections.abc import Iterator

    from graphrag_cache import Cache, CacheKeyCreator

    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsProcessor, MetricsStore
    from graphrag_llm.rate_limit import RateLimiter
    from graphrag_llm.retry import Retry
    from graphrag_llm.threading.embedding_thread_runner import (
        ThreadedLLMEmbeddingFunction,
        ThreadedLLMEmbeddingResponseHandler,
    )
    from graphrag_llm.tokenizer import Tokenizer
    from graphrag_llm.types import LLMEmbeddingArgs, LLMEmbeddingResponse


class LLMEmbedding(ABC):
    """Abstract base class for language model embeddings."""

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
        """Initialize the LLMEmbedding.

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
    def embedding(
        self, /, **kwargs: Unpack["LLMEmbeddingArgs"]
    ) -> "LLMEmbeddingResponse":
        """Sync embedding method."""
        raise NotImplementedError

    @abstractmethod
    async def embedding_async(
        self, /, **kwargs: Unpack["LLMEmbeddingArgs"]
    ) -> "LLMEmbeddingResponse":
        """Async embedding method."""
        raise NotImplementedError

    @contextmanager
    def embedding_thread_pool(
        self,
        *,
        response_handler: "ThreadedLLMEmbeddingResponseHandler",
        concurrency: int,
        queue_limit: int = 0,
    ) -> "Iterator[ThreadedLLMEmbeddingFunction]":
        """Run an embedding thread pool.

        Args
        ----
            response_handler: ThreadedLLMEmbeddingResponseHandler
                The callback function to handle embedding responses.
                (request_id, response|exception) -> Awaitable[None] | None
            concurrency: int
                The number of threads to spin up in a thread pool.
            queue_limit: int (default=0)
                The maximum number of items allowed in the input queue.
                0 means unlimited.
                Set this to a value to create backpressure on the caller.

        Yields
        ------
            ThreadedLLMEmbeddingFunction:
                A function that can be used to submit embedding requests to the thread pool.
                (input, request_id, **kwargs) -> None

                The thread pool will process the requests and invoke the provided callback
                with the responses.

                same signature as LLMEmbeddingFunction but requires a `request_id` parameter
                to identify the request and does not return anything.

        """
        with embedding_thread_runner(
            embedding=self.embedding,
            response_handler=response_handler,
            concurrency=concurrency,
            queue_limit=queue_limit,
            metrics_store=self.metrics_store,
        ) as embedding:
            yield embedding

    def embedding_batch(
        self,
        embedding_requests: list["LLMEmbeddingArgs"],
        *,
        concurrency: int,
        queue_limit: int = 0,
    ) -> list["LLMEmbeddingResponse | Exception"]:
        """Process a batch of embedding requests using a thread pool.

        Args
        ----
            embedding_requests: list[LLMEmbeddingArgs]
                A list of embedding request arguments to process in parallel.
            batch_size: int
                The number of inputs to process in each batch.
            concurrency: int
                The number of threads to spin up in a thread pool.
            queue_limit: int (default=0)
                The maximum number of items allowed in the input queue.
                0 means unlimited.
                Set this to a value to create backpressure on the caller.

        Returns
        -------
            list[LLMEmbeddingResponse | Exception]
                A list of embedding responses or exceptions for each input.
        """
        results: list[LLMEmbeddingResponse | Exception] = [None] * len(
            embedding_requests
        )  # type: ignore

        def handle_response(
            request_id: str,
            response: "LLMEmbeddingResponse | Exception",
        ) -> None:
            index = int(request_id)
            results[index] = response

        with self.embedding_thread_pool(
            response_handler=handle_response,
            concurrency=concurrency,
            queue_limit=queue_limit,
        ) as embedding:
            for idx, embedding_request in enumerate(embedding_requests):
                embedding(request_id=str(idx), **embedding_request)

        return results

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
