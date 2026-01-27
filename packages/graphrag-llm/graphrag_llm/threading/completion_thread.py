# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Completion Thread."""

import threading
from queue import Empty, Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from graphrag_llm.types import (
        LLMCompletionArgs,
        LLMCompletionChunk,
        LLMCompletionFunction,
        LLMCompletionResponse,
    )


LLMCompletionRequestQueue = Queue[tuple[str, "LLMCompletionArgs"] | None]
"""Input queue for LLM completions.

A queue for tracking requests to be made to a completion endpoint.
Each item in the queue is a tuple containing a request ID and a dictionary of
completion arguments. A `None` value indicates that the thread should terminate.

Queue Item Type:
    tuple[request_id, completion_args_dict] | None

Items in the queue are processed by a thread pool in which the results are placed
into an output queue to be handled by a response handler.
"""


LLMCompletionResponseQueue = Queue[
    tuple[
        str,
        "LLMCompletionResponse | Iterator[LLMCompletionChunk] | Exception",
    ]
    | None
]
"""Output queue for LLM completion responses.

A queue for tracking responses from completion requests. Each item in the queue is a tuple
containing the request ID and the corresponding response, which can be a full response,
a stream of chunks, or an exception if the request failed. A `None` value indicates that the
thread should terminate.

Queue Item Type:
    tuple[request_id, response | exception] | None

Items in the queue are produced by a thread pool that processes completion requests
from an input queue. This output queue is then consumed by a response handler provided
by the user.
"""


class CompletionThread(threading.Thread):
    """Thread for handling LLM completions."""

    def __init__(
        self,
        *,
        quit_process_event: threading.Event,
        input_queue: LLMCompletionRequestQueue,
        output_queue: LLMCompletionResponseQueue,
        completion: "LLMCompletionFunction",
    ) -> None:
        super().__init__()
        self._quit_process_event = quit_process_event
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._completion = completion

    def run(self):
        """Run the completion thread."""
        while True and not self._quit_process_event.is_set():
            try:
                input_data = self._input_queue.get(timeout=1)
            except Empty:
                continue
            if input_data is None:
                break
            request_id, data = input_data
            try:
                response = self._completion(**data)

                self._output_queue.put((request_id, response))
            except Exception as e:  # noqa: BLE001
                self._output_queue.put((request_id, e))
