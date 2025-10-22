# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Gather Completion Response Utility."""

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphrag_llm.types import (
        LLMCompletionChunk,
        LLMCompletionResponse,
    )


def gather_completion_response(
    response: "LLMCompletionResponse | Iterator[LLMCompletionChunk]",
) -> str:
    """Gather completion response from an iterator of response chunks.

    Args
    ----
        response: LMChatCompletion | Iterator[LLMChatCompletionChunk]
            The completion response or an iterator of response chunks.

    Returns
    -------
        The gathered response as a single string.
    """
    if isinstance(response, Iterator):
        return "".join(chunk.choices[0].delta.content or "" for chunk in response)

    return response.choices[0].message.content or ""


async def gather_completion_response_async(
    response: "LLMCompletionResponse | AsyncIterator[LLMCompletionChunk]",
) -> str:
    """Gather completion response from an iterator of response chunks.

    Args
    ----
        response: LMChatCompletion | AsyncIterator[LLMChatCompletionChunk]
            The completion response or an iterator of response chunks.

    Returns
    -------
        The gathered response as a single string.
    """
    if isinstance(response, AsyncIterator):
        gathered_content = ""
        async for chunk in response:
            gathered_content += chunk.choices[0].delta.content or ""

        return gathered_content

    return response.choices[0].message.content or ""
