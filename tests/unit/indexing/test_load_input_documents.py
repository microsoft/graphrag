# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

import asyncio
from dataclasses import dataclass
from typing import Any

from graphrag.index.workflows.load_input_documents import (
    load_input_documents,
    normalize_conversation_metadata,
)
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag_storage.tables.table import Table


@dataclass
class FakeDocument:
    id: str
    text: str
    title: str
    creation_date: str | None
    raw_data: dict[str, Any] | None = None


class FakeInputReader:
    def __init__(self, docs: list[FakeDocument]) -> None:
        self._docs = docs
        self._idx = 0

    def __aiter__(self):
        self._idx = 0
        return self

    async def __anext__(self):
        if self._idx >= len(self._docs):
            raise StopAsyncIteration
        doc = self._docs[self._idx]
        self._idx += 1
        return doc


class FakeTable(Table):
    def __init__(self) -> None:
        self.written: list[dict[str, Any]] = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration

    async def write(self, row: dict[str, Any]) -> None:
        self.written.append(row)

    async def has(self, row_id: str) -> bool:
        return False

    async def length(self) -> int:
        return len(self.written)

    async def close(self) -> None:
        return None


class TestNormalizeConversationMetadata:
    def test_preserves_existing_values(self):
        row = {
            "conversation_id": "conv-1",
            "turn_index": 7,
            "turn_timestamp": "2025-01-01T01:02:03Z",
            "turn_role": "assistant",
            "title": "ignore",
            "creation_date": "2025-01-01T00:00:00Z",
        }

        normalize_conversation_metadata(row, {})

        assert row["conversation_id"] == "conv-1"
        assert row["turn_index"] == 7
        assert row["turn_timestamp"] == "2025-01-01T01:02:03Z"
        assert row["turn_role"] == "assistant"

    def test_generates_defaults_when_missing(self):
        row = {
            "title": "conversation A",
            "creation_date": "2025-01-01T00:00:00Z",
            "raw_data": {},
        }

        normalize_conversation_metadata(row, {})

        assert row["conversation_id"] == gen_sha512_hash({"seed": "conversation A"}, ["seed"])
        assert row["turn_index"] == 0
        assert row["turn_timestamp"] == "2025-01-01T00:00:00Z"
        assert row["turn_role"] == "unknown"

    def test_conversation_id_falls_back_to_source_path(self):
        row = {
            "title": "",
            "creation_date": "",
            "raw_data": {"source_path": "./a/b/chat.jsonl"},
        }

        normalize_conversation_metadata(row, {})

        assert row["conversation_id"] == gen_sha512_hash(
            {"seed": "./a/b/chat.jsonl"},
            ["seed"],
        )


class TestLoadInputDocuments:
    def test_assigns_incremental_turn_index_per_conversation(self):
        docs = [
            FakeDocument(
                id="1",
                text="hello",
                title="same convo",
                creation_date="2025-01-01T00:00:00Z",
                raw_data={"meta": 1},
            ),
            FakeDocument(
                id="2",
                text="hi",
                title="same convo",
                creation_date="2025-01-01T00:00:01Z",
                raw_data={"meta": 2},
            ),
            FakeDocument(
                id="3",
                text="other",
                title="other convo",
                creation_date="2025-01-01T00:00:02Z",
                raw_data={"meta": 3},
            ),
        ]

        table = FakeTable()
        sample, count = asyncio.run(
            load_input_documents(FakeInputReader(docs), table, sample_size=5)
        )

        assert count == 3
        assert len(sample) == 3
        assert [row["turn_index"] for row in table.written] == [0, 1, 0]
        assert table.written[0]["raw_data"] == {"meta": 1}
        assert table.written[1]["raw_data"] == {"meta": 2}
        assert all("conversation_id" in row for row in table.written)
        assert all("turn_timestamp" in row for row in table.written)
        assert all("turn_role" in row for row in table.written)
