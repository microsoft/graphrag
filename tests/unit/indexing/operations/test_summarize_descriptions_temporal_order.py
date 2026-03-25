# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

import asyncio

from graphrag.index.operations.summarize_descriptions.description_summary_extractor import (
    SummarizeExtractor,
)
from graphrag.index.operations.summarize_descriptions.summarize_descriptions import (
    _stable_unique,
)


class _FakeTokenizer:
    def num_tokens(self, text: str) -> int:
        return len(text)


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeModel:
    def __init__(self):
        self.tokenizer = _FakeTokenizer()
        self.last_messages = ""

    async def completion_async(self, messages: str):
        self.last_messages = messages
        return _FakeResponse(content="summary")


def test_stable_unique_preserves_first_seen_order():
    values = ["latest", "old", "latest", "middle", "old"]
    assert _stable_unique(values) == ["latest", "old", "middle"]


def test_summarize_extractor_preserves_description_order_in_prompt_payload():
    model = _FakeModel()
    extractor = SummarizeExtractor(
        model=model,
        max_summary_length=200,
        max_input_tokens=10000,
        summarization_prompt="Descriptions: {description_list}",
    )

    result = asyncio.run(
        extractor(
            id="E1",
            descriptions=["first fact", "second update", "third correction"],
        )
    )

    assert result.description == "summary"
    assert (
        'Descriptions: ["first fact", "second update", "third correction"]'
        in model.last_messages
    )
