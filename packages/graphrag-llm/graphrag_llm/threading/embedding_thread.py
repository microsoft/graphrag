# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Embedding Thread."""

import threading
from queue import Empty, Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphrag_llm.types import (
        LLMEmbeddingArgs,
        LLMEmbeddingFunction,
        LLMEmbeddingResponse,
    )


LLMEmbeddingRequestQueue = Queue[tuple[str, "LLMEmbeddingArgs"] | None]
"""Input queue for LLM embeddings.

A queue for tracking requests to be made to an embedding endpoint.
Each item in the queue is a tuple containing a request ID and a dictionary of
embedding arguments. A `None` value indicates that the thread should terminate.

Queue Item Type:
    tuple[request_id, embedding_args_dict] | None

Items in the queue are processed by a thread pool in which the results are placed
into an output queue to be handled by a response handler.
"""

LLMEmbeddingResponseQueue = Queue[
    tuple[
        str,
        "LLMEmbeddingResponse | Exception",
    ]
    | None
]
"""Output queue for LLM embedding responses.

A queue for tracking responses from embedding requests. Each item in the queue is a tuple
containing the request ID and the corresponding response, which can be a full response
or an exception if the request failed. A `None` value indicates that the
thread should terminate.

Queue Item Type:
    tuple[request_id, response | exception] | None

Items in the queue are produced by a thread pool that processes embedding requests
from an input queue. This output queue is then consumed by a response handler provided
by the user.
"""


class EmbeddingThread(threading.Thread):
    """Thread for handling LLM embeddings."""

    def __init__(
        self,
        *,
        quit_process_event: threading.Event,
        input_queue: LLMEmbeddingRequestQueue,
        output_queue: LLMEmbeddingResponseQueue,
        embedding: "LLMEmbeddingFunction",
    ) -> None:
        super().__init__()
        self._quit_process_event = quit_process_event
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._embedding = embedding

    def run(self) -> None:
        """Run the embedding thread."""
        while not self._quit_process_event.is_set():
            try:
                input_data = self._input_queue.get(timeout=0.1)
            except Empty:
                continue

            if input_data is None:
                break
            request_id, data = input_data
            try:
                response = self._embedding(**data)

                self._output_queue.put((request_id, response))
            except Exception as e:  # noqa: BLE001
                self._output_queue.put((request_id, e))
