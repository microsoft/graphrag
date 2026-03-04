# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for _filter_under_community_level preserving NaN-level nodes."""

import numpy as np
import pandas as pd

from graphrag.query.indexer_adapters import _filter_under_community_level


def test_filter_preserves_nan_level_nodes():
    """Nodes with level=NaN should not be discarded by the filter.

    Regression test for issue #1808 where isolated nodes without a community
    assignment (level=None) were incorrectly dropped.
    """
    df = pd.DataFrame({
        "id": ["a", "b", "c", "d"],
        "level": [0, 1, 2, np.nan],
        "community": [1, 2, 3, np.nan],
    })

    result = _filter_under_community_level(df, community_level=1)

    # Should keep level 0, 1 (<=1) and NaN (unassigned)
    assert len(result) == 3
    assert set(result["id"].tolist()) == {"a", "b", "d"}


def test_filter_excludes_higher_level_nodes():
    """Nodes with level > community_level should be excluded."""
    df = pd.DataFrame({
        "id": ["a", "b", "c"],
        "level": [0, 2, 3],
        "community": [1, 2, 3],
    })

    result = _filter_under_community_level(df, community_level=1)

    assert len(result) == 1
    assert result["id"].tolist() == ["a"]
