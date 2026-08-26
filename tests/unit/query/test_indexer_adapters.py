# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pandas as pd

from graphrag.query.indexer_adapters import _filter_under_community_level


def test_filter_under_community_level_preserves_nan():
    """Entities without community assignment (level=NaN) should be preserved."""
    df = pd.DataFrame({"id": [1, 2, 3], "level": [0.0, float("nan"), 2.0]})
    result = _filter_under_community_level(df, 2)
    assert len(result) == 3
    assert result["id"].tolist() == [1, 2, 3]


def test_filter_under_community_level_filters_above_level():
    """Entities with level above community_level should be filtered out."""
    df = pd.DataFrame({"id": [1, 2, 3], "level": [0.0, 1.0, 3.0]})
    result = _filter_under_community_level(df, 2)
    assert len(result) == 2
    assert result["id"].tolist() == [1, 2]


def test_filter_under_community_level_all_below():
    """All entities within the community level should be preserved."""
    df = pd.DataFrame({"id": [1, 2], "level": [0.0, 1.0]})
    result = _filter_under_community_level(df, 2)
    assert len(result) == 2


def test_filter_under_community_level_all_nan():
    """When all levels are NaN (no community assignments), all entities should be preserved."""
    df = pd.DataFrame({"id": [1, 2], "level": [float("nan"), float("nan")]})
    result = _filter_under_community_level(df, 2)
    assert len(result) == 2


def test_filter_under_community_level_mixed_with_nan():
    """Mix of NaN and above-threshold levels should preserve NaN and drop above-threshold."""
    df = pd.DataFrame({"id": [1, 2, 3], "level": [0.0, float("nan"), 5.0]})
    result = _filter_under_community_level(df, 2)
    assert len(result) == 2
    assert result["id"].tolist() == [1, 2]
