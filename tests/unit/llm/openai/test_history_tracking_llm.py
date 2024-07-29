# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""History-tracking LLM Tests."""

import asyncio
from typing import cast

from graphrag.llm import CompletionLLM, LLMOutput
from graphrag.llm.openai.openai_history_tracking_llm import OpenAIHistoryTrackingLLM


async def test_history_tracking_llm() -> None:
    async def mock_responder(input: str, **kwargs: dict) -> LLMOutput:
        await asyncio.sleep(0.0001)
        return LLMOutput(output=f"response to [{input}]")

    delegate = cast(CompletionLLM, mock_responder)
    llm = OpenAIHistoryTrackingLLM(delegate)

    response = await llm("input 1")
    history: list[dict] = cast(list[dict], response.history)
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "input 1"}
    assert history[1] == {"role": "assistant", "content": "response to [input 1]"}

    response = await llm("input 2", history=history)
    history: list[dict] = cast(list[dict], response.history)
    assert len(history) == 4
    assert history[0] == {"role": "user", "content": "input 1"}
    assert history[1] == {"role": "assistant", "content": "response to [input 1]"}
    assert history[2] == {"role": "user", "content": "input 2"}
    assert history[3] == {"role": "assistant", "content": "response to [input 2]"}
