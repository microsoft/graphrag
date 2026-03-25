# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

from graphrag_chunking.text_chunk import TextChunk

from graphrag.index.workflows.create_base_text_units import (
    _chunk_temporal_metadata,
    _infer_turn_spans,
)
from graphrag.data_model.schemas import TEXT_UNITS_FINAL_COLUMNS


def test_infer_turn_spans_from_dialogue_markers():
    doc = {
        "text": "User: hello\nAssistant: hi there\nUser: thanks",
        "turn_index": 5,
        "turn_timestamp": "2026-01-01T00:00:00Z",
    }

    spans = _infer_turn_spans(doc)

    # row 1개를 turn 1개로 보기 때문에 span은 항상 1개여야 한다.
    assert len(spans) == 1
    assert spans[0]["turn_role"] == "user"
    assert spans[0]["turn_index"] == 5


def test_infer_turn_spans_from_unlabeled_paragraph_blocks():
    doc = {
        "text": "안녕\n\n반가워\n\n오늘 일정 알려줘",
        "turn_index": 10,
        "turn_timestamp": "2026-01-01T00:00:00Z",
    }

    spans = _infer_turn_spans(doc)

    assert len(spans) == 1
    assert spans[0]["turn_index"] == 10
    assert spans[0]["turn_role"] == "unknown"


def test_infer_turn_spans_without_boundaries_falls_back_to_single_span():
    doc = {
        "text": "라벨이나 빈 줄 구분이 없는 단일 블록 텍스트",
        "turn_index": 7,
        "turn_timestamp": "2026-01-01T00:00:00Z",
        "turn_role": "assistant",
    }

    spans = _infer_turn_spans(doc)

    assert len(spans) == 1
    assert spans[0]["turn_index"] == 7
    assert spans[0]["turn_role"] == "assistant"


def test_infer_turn_spans_from_json_raw_data_messages():
    doc = {
        "text": "안녕? 반가워! 오늘 일정 알려줘",
        "turn_index": 0,
        "turn_timestamp": "2026-01-01T00:00:00Z",
        "raw_data": {
            "messages": [
                {
                    "role": "user",
                    "content": "안녕?",
                    "timestamp": "2026-01-01T00:00:00Z",
                },
                {
                    "role": "assistant",
                    "content": "반가워!",
                    "timestamp": "2026-01-01T00:01:00Z",
                },
                {
                    "role": "user",
                    "content": "오늘 일정 알려줘",
                    "timestamp": "2026-01-01T00:02:00Z",
                },
            ]
        },
    }

    spans = _infer_turn_spans(doc)

    # raw_data에 배열이 있어도 현재 정책은 row 1개 = turn 1개
    assert len(spans) == 1
    assert spans[0]["turn_index"] == 0
    assert spans[0]["turn_role"] == "unknown"
    assert spans[0]["turn_timestamp"] == "2026-01-01T00:00:00Z"


def test_chunk_temporal_metadata_maps_turn_range_and_roles():
    doc = {
        "turn_index": 0,
        "turn_timestamp": "2026-01-01T00:00:00Z",
        "turn_role": "unknown",
    }
    turn_spans = [
        {
            "start_char": 0,
            "end_char": 10,
            "turn_index": 0,
            "turn_timestamp": "2026-01-01T00:00:00Z",
            "turn_role": "user",
        },
        {
            "start_char": 10,
            "end_char": 20,
            "turn_index": 1,
            "turn_timestamp": "2026-01-01T00:01:00Z",
            "turn_role": "assistant",
        },
    ]
    chunk = TextChunk(
        original="hello world",
        text="hello world",
        index=0,
        start_char=5,
        end_char=15,
        token_count=2,
    )

    temporal = _chunk_temporal_metadata(doc, turn_spans, chunk)

    assert temporal["start_turn_index"] == 0
    assert temporal["end_turn_index"] == 1
    assert temporal["turn_timestamp_start"] == "2026-01-01T00:00:00Z"
    assert temporal["turn_timestamp_end"] == "2026-01-01T00:01:00Z"
    assert temporal["included_roles"] == ["assistant", "user"]


def test_chunk_temporal_metadata_is_stable_with_unsorted_turn_spans():
    doc = {
        "turn_index": 0,
        "turn_timestamp": "2026-01-01T00:00:00Z",
        "turn_role": "unknown",
    }
    turn_spans = [
        {
            "start_char": 10,
            "end_char": 20,
            "turn_index": 2,
            "turn_timestamp": "2026-01-01T00:02:00Z",
            "turn_role": "ASSISTANT",
        },
        {
            "start_char": 0,
            "end_char": 10,
            "turn_index": 1,
            "turn_timestamp": "2026-01-01T00:01:00Z",
            "turn_role": "USER",
        },
    ]
    chunk = TextChunk(
        original="hello world",
        text="hello world",
        index=0,
        start_char=0,
        end_char=20,
        token_count=2,
    )

    temporal = _chunk_temporal_metadata(doc, turn_spans, chunk)

    assert temporal["start_turn_index"] == 1
    assert temporal["end_turn_index"] == 2
    assert temporal["turn_timestamp_start"] == "2026-01-01T00:01:00Z"
    assert temporal["turn_timestamp_end"] == "2026-01-01T00:02:00Z"
    assert temporal["included_roles"] == ["assistant", "user"]


def test_final_text_unit_schema_contains_temporal_columns():
    for required in [
        "start_turn_index",
        "end_turn_index",
        "turn_timestamp_start",
        "turn_timestamp_end",
        "included_roles",
        "chunk_index_in_document",
        "chunk_index_in_conversation",
    ]:
        assert required in TEXT_UNITS_FINAL_COLUMNS
