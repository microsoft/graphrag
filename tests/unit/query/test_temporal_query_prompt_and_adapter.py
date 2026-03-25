# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

import pandas as pd

from graphrag.prompts.query.local_search_system_prompt import LOCAL_SEARCH_SYSTEM_PROMPT
from graphrag.query.indexer_adapters import read_indexer_text_units


def test_local_search_prompt_mentions_current_history_and_superseded():
    assert "CURRENT STATE" in LOCAL_SEARCH_SYSTEM_PROMPT
    assert "TIMELINE / HISTORY" in LOCAL_SEARCH_SYSTEM_PROMPT
    assert "SUPERSEDED FACTS" in LOCAL_SEARCH_SYSTEM_PROMPT


def test_read_indexer_text_units_preserves_temporal_attributes():
    df = pd.DataFrame(
        [
            {
                "id": "tu1",
                "text": "hello",
                "n_tokens": 1,
                "document_id": "doc1",
                "start_turn_index": 1,
                "end_turn_index": 1,
                "chunk_index_in_conversation": 0,
            }
        ]
    )

    units = read_indexer_text_units(df)

    assert units[0].attributes is not None
    assert units[0].attributes["start_turn_index"] == 1
    assert units[0].attributes["end_turn_index"] == 1
