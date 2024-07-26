# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Caching LLM Tests."""

import asyncio
from typing import Any, cast

from graphrag.llm import CompletionLLM, LLMOutput
from graphrag.llm.base.caching_llm import CachingLLM
from graphrag.llm.openai.openai_history_tracking_llm import OpenAIHistoryTrackingLLM
from graphrag.llm.types import LLMCache


class TestCache(LLMCache):
    def __init__(self):
        self.cache = {}

    async def has(self, key: str) -> bool:
        return key in self.cache

    async def get(self, key: str) -> dict | None:
        entry = self.cache.get(key)
        return entry["result"] if entry else None

    async def set(
        self, key: str, value: str, debug_data: dict[str, Any] | None = None
    ) -> None:
        self.cache[key] = {"result": value, **(debug_data or {})}


async def mock_responder(input: str, **kwargs: dict) -> LLMOutput:
    await asyncio.sleep(0.0001)
    return LLMOutput(output=f"response to [{input}]")


def throwing_responder(input: str, **kwargs: dict) -> LLMOutput:
    raise ValueError


mock_responder_llm = cast(CompletionLLM, mock_responder)
throwing_llm = cast(CompletionLLM, throwing_responder)


async def test_caching_llm() -> None:
    """Test a composite LLM."""
    llm = CachingLLM(
        mock_responder_llm, llm_parameters={}, operation="test", cache=TestCache()
    )
    response = await llm("input 1")
    assert response.output == "response to [input 1]"
    llm.set_delegate(throwing_llm)
    response = await llm("input 1")
    assert response.output == "response to [input 1]"


async def test_composite_llm() -> None:
    """Test a composite LLM."""
    caching = CachingLLM(
        mock_responder_llm, llm_parameters={}, operation="test", cache=TestCache()
    )
    llm = OpenAIHistoryTrackingLLM(caching)

    response = await llm("input 1")
    history: list[dict] = cast(list[dict], response.history)
    assert len(history) == 2

    response = await llm("input 1")
    history: list[dict] = cast(list[dict], response.history)
    assert len(history) == 2

    response = await llm("input 2", history=history)
    history: list[dict] = cast(list[dict], response.history)
    assert len(history) == 4
