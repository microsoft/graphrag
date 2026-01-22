# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Create completion response."""

from graphrag_llm.types import (
    LLMChoice,
    LLMCompletionMessage,
    LLMCompletionResponse,
    LLMCompletionUsage,
)


def create_completion_response(response: str) -> LLMCompletionResponse:
    """Create a completion response object.

    Args:
        response: The completion response string.

    Returns
    -------
        LLMCompletionResponse: The completion response object.
    """
    return LLMCompletionResponse(
        id="completion-id",
        object="chat.completion",
        created=0,
        model="mock-model",
        choices=[
            LLMChoice(
                index=0,
                message=LLMCompletionMessage(
                    role="assistant",
                    content=response,
                ),
                finish_reason="stop",
            )
        ],
        usage=LLMCompletionUsage(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        ),
        formatted_response=None,
    )
