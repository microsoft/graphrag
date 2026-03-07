# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import numpy as np
import pandas as pd
from graphrag.query.indexer_adapters import (
    _filter_under_community_level,
    read_indexer_entities,
)


def test_filter_under_community_level_keeps_nan_levels():
    df = pd.DataFrame({
        "id": ["1", "2", "3", "4"],
        "level": [0, 1, 2, np.nan],
    })
    result = _filter_under_community_level(df, 1)
    assert len(result) == 3
    assert set(result["id"].tolist()) == {"1", "2", "4"}


def test_filter_under_community_level_filters_above():
    df = pd.DataFrame({
        "id": ["1", "2", "3"],
        "level": [0, 1, 2],
    })
    result = _filter_under_community_level(df, 1)
    assert len(result) == 2
    assert set(result["id"].tolist()) == {"1", "2"}


def test_filter_under_community_level_all_nan():
    df = pd.DataFrame({
        "id": ["1", "2"],
        "level": [np.nan, np.nan],
    })
    result = _filter_under_community_level(df, 1)
    assert len(result) == 2


def test_read_indexer_entities_preserves_entities_without_community():
    entities = pd.DataFrame({
        "id": ["e1", "e2", "e3"],
        "title": ["Entity1", "Entity2", "Entity3"],
        "type": ["TYPE_A", "TYPE_B", "TYPE_C"],
        "human_readable_id": [0, 1, 2],
        "description": ["desc1", "desc2", "desc3"],
        "degree": [3, 2, 1],
        "text_unit_ids": [["tu1"], ["tu2"], ["tu3"]],
        "description_embedding": [None, None, None],
    })
    communities = pd.DataFrame({
        "id": ["c1"],
        "community": [0],
        "level": [0],
        "entity_ids": [["e1", "e2"]],
        "title": ["Community1"],
    })

    result = read_indexer_entities(entities, communities, community_level=0)
    result_ids = {e.id for e in result}
    assert result_ids == {"e1", "e2", "e3"}
