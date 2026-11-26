# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for _filter_under_community_level logic."""

import pandas as pd


def _filter_under_community_level(
    df: pd.DataFrame, community_level: int
) -> pd.DataFrame:
    return df[(df.level <= community_level) | df.level.isna()]


def test_filter_under_community_level_preserves_nan():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "level": [0, 1, None, 2],
            "title": ["a", "b", "c", "d"],
        }
    )
    result = _filter_under_community_level(df, 1)
    assert len(result) == 3
    assert result["id"].tolist() == [1, 2, 3]


def test_filter_under_community_level_all_assigned():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "level": [0, 1, 2],
            "title": ["a", "b", "c"],
        }
    )
    result = _filter_under_community_level(df, 1)
    assert len(result) == 2
    assert result["id"].tolist() == [1, 2]


def test_filter_under_community_level_all_nan():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "level": [None, None, None],
            "title": ["a", "b", "c"],
        }
    )
    result = _filter_under_community_level(df, 1)
    assert len(result) == 3
