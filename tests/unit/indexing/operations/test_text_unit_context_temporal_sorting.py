# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

import pandas as pd

import graphrag.data_model.schemas as schemas
from graphrag.index.operations.summarize_communities.text_unit_context.prep_text_units import (
    prep_text_units,
)
from graphrag.index.operations.summarize_communities.text_unit_context.sort_context import (
    sort_context,
)


class _FakeTokenizer:
    def num_tokens(self, text: str) -> int:
        return len(text)


def test_prep_text_units_includes_temporal_fields_in_all_details():
    text_units = pd.DataFrame(
        [
            {
                "id": "t1",
                "human_readable_id": 1,
                "text": "first",
                "start_turn_index": 1,
                "end_turn_index": 1,
                "turn_timestamp_start": "2026-01-01T09:00:00Z",
                "turn_timestamp_end": "2026-01-01T09:00:30Z",
                "chunk_index_in_conversation": 0,
            }
        ]
    )
    nodes = pd.DataFrame(
        [
            {
                "id": "n1",
                "title": "Entity",
                "community": 1,
                "degree": 3,
                "text_unit_ids": ["t1"],
            }
        ]
    )

    out = prep_text_units(text_units, nodes)
    details = out.iloc[0][schemas.ALL_DETAILS]

    assert details[schemas.START_TURN_INDEX] == 1
    assert details[schemas.END_TURN_INDEX] == 1
    assert details[schemas.TURN_TIMESTAMP_START] == "2026-01-01T09:00:00Z"
    assert details[schemas.TURN_TIMESTAMP_END] == "2026-01-01T09:00:30Z"


def test_sort_context_prioritizes_temporal_order_over_degree():
    context = [
        {
            "id": 2,
            "text": "later but high degree",
            "entity_degree": 100,
            "start_turn_index": 5,
            "turn_timestamp_start": "2026-01-01T10:00:00Z",
            "chunk_index_in_conversation": 1,
        },
        {
            "id": 1,
            "text": "earlier lower degree",
            "entity_degree": 1,
            "start_turn_index": 1,
            "turn_timestamp_start": "2026-01-01T09:00:00Z",
            "chunk_index_in_conversation": 0,
        },
    ]

    out = sort_context(context, tokenizer=_FakeTokenizer())

    first_data_line = out.splitlines()[2]
    assert first_data_line.startswith("1,")
