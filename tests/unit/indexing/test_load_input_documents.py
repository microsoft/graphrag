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

        assert row["conversation_id"] == gen_sha512_hash({"seed": "conversation"}, ["seed"])
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
            {"seed": "chat"},
            ["seed"],
        )

    def test_source_path_prefix_is_case_sensitive(self):
        upper = {
            "title": "",
            "creation_date": "",
            "raw_data": {"source_path": "./a/b/Chat_file.json"},
        }
        lower = {
            "title": "",
            "creation_date": "",
            "raw_data": {"source_path": "./a/b/chat_file.json"},
        }

        normalize_conversation_metadata(upper, {})
        normalize_conversation_metadata(lower, {})

        assert upper["conversation_id"] != lower["conversation_id"]

    def test_treats_blank_values_as_missing(self):
        row = {
            "title": "conversation B",
            "creation_date": "2025-01-02T00:00:00Z",
            "conversation_id": " ",
            "turn_index": " ",
            "turn_timestamp": " ",
            "turn_role": " ",
            "raw_data": {},
        }

        normalize_conversation_metadata(row, {})

        assert row["conversation_id"] == gen_sha512_hash({"seed": "conversation"}, ["seed"])
        assert row["turn_index"] == 0
        assert row["turn_timestamp"] == "2025-01-02T00:00:00Z"
        assert row["turn_role"] == "unknown"

    def test_conversation_id_falls_back_to_document_id(self):
        row = {
            "id": "doc-001",
            "title": "",
            "creation_date": "2025-01-03T00:00:00Z",
            "raw_data": {},
        }

        normalize_conversation_metadata(row, {})

        assert row["conversation_id"] == gen_sha512_hash({"seed": "doc-001"}, ["seed"])

    def test_reads_conversation_fields_from_raw_data(self):
        row = {
            "id": "doc-002",
            "title": "fallback title",
            "creation_date": "2025-01-04T00:00:00Z",
            "raw_data": {
                "conversation_id": "csv-conv-1",
                "turn_index": 42,
                "turn_timestamp": "2025-01-04T09:00:00Z",
                "turn_role": "user",
            },
        }

        normalize_conversation_metadata(row, {})

        assert row["conversation_id"] == "csv-conv-1"
        assert row["turn_index"] == 42
        assert row["turn_timestamp"] == "2025-01-04T09:00:00Z"
        assert row["turn_role"] == "user"


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

    def test_prefers_raw_data_conversation_values(self):
        docs = [
            FakeDocument(
                id="1",
                text="hello",
                title="fallback convo",
                creation_date="2025-01-01T00:00:00Z",
                raw_data={
                    "conversation_id": "thread-7",
                    "turn_index": 10,
                    "turn_timestamp": "2025-01-01T12:00:00Z",
                    "turn_role": "assistant",
                },
            )
        ]

        table = FakeTable()
        sample, count = asyncio.run(
            load_input_documents(FakeInputReader(docs), table, sample_size=5)
        )

        assert count == 1
        assert len(sample) == 1
        assert table.written[0]["conversation_id"] == "thread-7"
        assert table.written[0]["turn_index"] == 10
        assert table.written[0]["turn_timestamp"] == "2025-01-01T12:00:00Z"
        assert table.written[0]["turn_role"] == "assistant"

    def test_default_titles_from_same_file_share_conversation_id(self):
        docs = [
            FakeDocument(
                id="1",
                text="hello",
                title="sample_data.json (0)",
                creation_date="2025-01-01T00:00:00Z",
                raw_data={},
            ),
            FakeDocument(
                id="2",
                text="world",
                title="sample_data.json (1)",
                creation_date="2025-01-01T00:00:01Z",
                raw_data={},
            ),
        ]

        table = FakeTable()
        sample, count = asyncio.run(
            load_input_documents(FakeInputReader(docs), table, sample_size=5)
        )

        assert count == 2
        assert len(sample) == 2
        assert table.written[0]["conversation_id"] == table.written[1]["conversation_id"]
        assert [row["turn_index"] for row in table.written] == [0, 1]
