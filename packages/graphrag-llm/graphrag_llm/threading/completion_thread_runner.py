# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Completion Thread Runner."""

import asyncio
import sys
import threading
import time
from collections.abc import Awaitable, Iterator
from contextlib import contextmanager
from queue import Empty, Queue
from typing import TYPE_CHECKING, Protocol, Unpack, runtime_checkable

from graphrag_llm.threading.completion_thread import CompletionThread

if TYPE_CHECKING:
    from graphrag_llm.metrics import MetricsStore
    from graphrag_llm.threading.completion_thread import (
        LLMCompletionRequestQueue,
        LLMCompletionResponseQueue,
    )
    from graphrag_llm.types import (
        LLMCompletionArgs,
        LLMCompletionChunk,
        LLMCompletionFunction,
        LLMCompletionResponse,
    )


@runtime_checkable
class ThreadedLLMCompletionResponseHandler(Protocol):
    """Threaded completion response handler.

    This function is used to handle responses from the threaded completion runner.

    Args
    ----
        request_id: str
            The request ID associated with the completion request.
        resp: LLMCompletionResponse | Iterator[LLMCompletionChunk] | Exception
            The completion response, which can be a full response, a stream of chunks,
            or an exception if the request failed.

    Returns
    -------
        Awaitable[None] | None
            The callback can be asynchronous or synchronous.
    """

    def __call__(
        self,
        request_id: str,
        response: "LLMCompletionResponse | Iterator[LLMCompletionChunk] | Exception",
        /,
    ) -> Awaitable[None] | None:
        """Threaded completion response handler."""
        ...


@runtime_checkable
class ThreadedLLMCompletionFunction(Protocol):
    """Threaded completion function.

    This function is used to submit requests to a thread pool for processing.
    The thread pool will process the requests and invoke the provided callback
    with the responses.

    same signature as LLMCompletionFunction but requires a `request_id` parameter
    to identify the request and does not return anything.

    Args
    ----
        messages: LLMCompletionMessagesParam
            The messages to send to the LLM.
            Can be str | list[dict[str, str]] | list[ChatCompletionMessageParam].
        request_id: str
            The request ID to associate with the completion request.
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
        None
    """

    def __call__(
        self,
        /,
        request_id: str,
        **kwargs: Unpack["LLMCompletionArgs"],
    ) -> None:
        """Threaded Chat completion function."""
        ...


def _start_completion_thread_pool(
    *,
    completion: "LLMCompletionFunction",
    quit_process_event: threading.Event,
    concurrency: int,
    queue_limit: int,
) -> tuple[
    list[CompletionThread],
    "LLMCompletionRequestQueue",
    "LLMCompletionResponseQueue",
]:
    threads: list[CompletionThread] = []
    input_queue: LLMCompletionRequestQueue = Queue(queue_limit)
    output_queue: LLMCompletionResponseQueue = Queue()
    for _ in range(concurrency):
        thread = CompletionThread(
            quit_process_event=quit_process_event,
            input_queue=input_queue,
            output_queue=output_queue,
            completion=completion,
        )
        thread.start()
        threads.append(thread)

    return threads, input_queue, output_queue


@contextmanager
def completion_thread_runner(
    *,
    completion: "LLMCompletionFunction",
    response_handler: ThreadedLLMCompletionResponseHandler,
    concurrency: int,
    queue_limit: int = 0,
    metrics_store: "MetricsStore | None" = None,
) -> Iterator[ThreadedLLMCompletionFunction]:
    """Run a completion thread pool.

    Args
    ----
        completion: LLMCompletion
            The LLMCompletion instance to use for processing requests.
        response_handler: ThreadedLLMCompletionResponseHandler
            The callback function to handle completion responses.
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
        ThreadedLLMCompletionFunction:
            A function that can be used to submit completion requests to the thread pool.
            (messages, request_id, **kwargs) -> None

            The thread pool will process the requests and invoke the provided callback
            with the responses.

            same signature as LLMCompletionFunction but requires a `request_id` parameter
            to identify the request and does not return anything.
    """
    quit_process_event = threading.Event()
    threads, input_queue, output_queue = _start_completion_thread_pool(
        completion=completion,
        quit_process_event=quit_process_event,
        concurrency=concurrency,
        queue_limit=queue_limit,
    )

    def _process_output(
        quit_process_event: threading.Event,
        output_queue: "LLMCompletionResponseQueue",
        callback: ThreadedLLMCompletionResponseHandler,
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

    def _process_input(request_id: str, **kwargs: Unpack["LLMCompletionArgs"]):
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
