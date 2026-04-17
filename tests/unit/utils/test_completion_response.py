# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import asyncio

from graphrag_llm.types import LLMCompletionResponse
from graphrag_llm.utils import (
    gather_completion_response,
    gather_completion_response_async,
    structure_completion_response,
)
from pydantic import BaseModel


class RatingResponse(BaseModel):
    rating: int


def _create_completion_response(
    *,
    content: str | None,
    tool_call_arguments: str | None = None,
) -> LLMCompletionResponse:
    message: dict = {
        "role": "assistant",
        "content": content,
    }

    if tool_call_arguments is not None:
        message["tool_calls"] = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "structured_output",
                    "arguments": tool_call_arguments,
                },
            }
        ]

    return LLMCompletionResponse(
        id="completion-id",
        object="chat.completion",
        created=0,
        model="mock-model",
        choices=[
            {
                "index": 0,
                "message": message,
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        formatted_response=None,
    )


def test_content_prefers_message_content() -> None:
    response = _create_completion_response(
        content="plain text",
        tool_call_arguments='{"rating": 9}',
    )

    assert response.content == "plain text"


def test_content_falls_back_to_function_tool_call_arguments() -> None:
    response = _create_completion_response(
        content=None,
        tool_call_arguments='{"rating": 7}',
    )

    assert response.content == '{"rating": 7}'


def test_gather_completion_response_falls_back_to_tool_call_arguments() -> None:
    response = _create_completion_response(
        content=None,
        tool_call_arguments='{"rating": 3}',
    )

    assert gather_completion_response(response) == '{"rating": 3}'


def test_gather_completion_response_async_falls_back_to_tool_call_arguments() -> None:
    response = _create_completion_response(
        content=None,
        tool_call_arguments='{"rating": 5}',
    )

    gathered_response = asyncio.run(gather_completion_response_async(response))
    assert gathered_response == '{"rating": 5}'


def test_structure_completion_response_uses_tool_call_arguments() -> None:
    response = _create_completion_response(
        content=None,
        tool_call_arguments='{"rating": 11}',
    )

    parsed = structure_completion_response(response.content, RatingResponse)
    assert parsed.rating == 11
