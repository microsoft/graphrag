# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Embedding Thread Runner."""

import asyncio
import sys
import threading
import time
from collections.abc import Awaitable, Iterator
from contextlib import contextmanager
from queue import Empty, Queue
from typing import TYPE_CHECKING, Protocol, Unpack, runtime_checkable

from graphrag_llm.threading.embedding_thread import EmbeddingThread

if TYPE_CHECKING:
    from graphrag_llm.metrics import MetricsStore
    from graphrag_llm.threading.embedding_thread import (
        LLMEmbeddingRequestQueue,
        LLMEmbeddingResponseQueue,
    )
    from graphrag_llm.types import (
        LLMEmbeddingArgs,
        LLMEmbeddingFunction,
        LLMEmbeddingResponse,
    )


@runtime_checkable
class ThreadedLLMEmbeddingResponseHandler(Protocol):
    """Threaded embedding response handler.

    This function is used to handle responses from the threaded embedding runner.

    Args
    ----
        request_id: str
            The request ID associated with the embedding request.
        resp: LLMEmbeddingResponse | Exception
            The embedding response, which can be a full response or
            an exception if the request failed.

    Returns
    -------
        Awaitable[None] | None
            The callback can be asynchronous or synchronous.
    """

    def __call__(
        self,
        request_id: str,
        response: "LLMEmbeddingResponse | Exception",
        /,
    ) -> Awaitable[None] | None:
        """Threaded embedding response handler."""
        ...


@runtime_checkable
class ThreadedLLMEmbeddingFunction(Protocol):
    """Threaded embedding function.

    This function is used to make embedding requests in a threaded context.

    Args
    ----
        request_id: str
            The request ID associated with the embedding request.
        input: list[str]
            The input texts to be embedded.
        **kwargs: Any
            Additional keyword arguments.

    Returns
    -------
        LLMEmbeddingResponse
            The embedding response.
    """

    def __call__(
        self, /, request_id: str, **kwargs: Unpack["LLMEmbeddingArgs"]
    ) -> None:
        """Threaded embedding function."""
        ...


def _start_embedding_thread_pool(
    *,
    embedding: "LLMEmbeddingFunction",
    quit_process_event: threading.Event,
    concurrency: int,
    queue_limit: int,
) -> tuple[
    list["EmbeddingThread"],
    "LLMEmbeddingRequestQueue",
    "LLMEmbeddingResponseQueue",
]:
    threads: list[EmbeddingThread] = []
    input_queue: LLMEmbeddingRequestQueue = Queue(queue_limit)
    output_queue: LLMEmbeddingResponseQueue = Queue()
    for _ in range(concurrency):
        thread = EmbeddingThread(
            quit_process_event=quit_process_event,
            input_queue=input_queue,
            output_queue=output_queue,
            embedding=embedding,
        )
        thread.start()
        threads.append(thread)

    return threads, input_queue, output_queue


@contextmanager
def embedding_thread_runner(
    *,
    embedding: "LLMEmbeddingFunction",
    response_handler: ThreadedLLMEmbeddingResponseHandler,
    concurrency: int,
    queue_limit: int = 0,
    metrics_store: "MetricsStore | None" = None,
) -> Iterator[ThreadedLLMEmbeddingFunction]:
    """Run an embedding thread pool.

    Args
    ----
        embedding: LLMEmbeddingFunction
            The LLMEmbeddingFunction instance to use for processing requests.
        response_handler: ThreadedLLMEmbeddingResponseHandler
            The callback function to handle embedding responses.
            (request_id, response|exception) -> Awaitable[None] | None
        concurrency: int
            The number of threads to spin up in a thread pool.
        queue_limit: int (default=0)
            The maximum number of items allowed in the input queue.
            0 means unlimited.
            Set this to a value to create backpressure on the caller.
        metrics_store: MetricsStore | None (default=None)
            Optional metrics store to record runtime duration.

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
    quit_process_event = threading.Event()
    threads, input_queue, output_queue = _start_embedding_thread_pool(
        embedding=embedding,
        quit_process_event=quit_process_event,
        concurrency=concurrency,
        queue_limit=queue_limit,
    )

    def _process_output(
        quit_process_event: threading.Event,
        output_queue: "LLMEmbeddingResponseQueue",
        callback: ThreadedLLMEmbeddingResponseHandler,
    ):
        while True and not quit_process_event.is_set():
            try:
                data = output_queue.get(timeout=1)
            except Empty:
                continue
            if data is None:
                break
            request_id, response = data
            response = callback(request_id, response)

            if asyncio.iscoroutine(response):
                response = asyncio.run(response)

    def _process_input(request_id: str, **kwargs: Unpack["LLMEmbeddingArgs"]):
        if not request_id:
            msg = "request_id needs to be passed as a keyword argument"
            raise ValueError(msg)
        input_queue.put((request_id, kwargs))

    handle_response_thread = threading.Thread(
        target=_process_output,
        args=(quit_process_event, output_queue, response_handler),
    )
    handle_response_thread.start()

    def _cleanup():
        for _ in threads:
            input_queue.put(None)

        for thread in threads:
            while thread.is_alive():
                thread.join(timeout=1)

        output_queue.put(None)

        while handle_response_thread.is_alive():
            handle_response_thread.join(timeout=1)

    start_time = time.time()
    try:
        yield _process_input
        _cleanup()
    except KeyboardInterrupt:
        quit_process_event.set()
        sys.exit(1)
    finally:
        end_time = time.time()
        runtime = end_time - start_time
        if metrics_store:
            metrics_store.update_metrics(metrics={"runtime_duration_seconds": runtime})
