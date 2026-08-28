# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pandas as pd
from graphrag.query.indexer_adapters import _filter_under_community_level


def test_filter_under_community_level_keeps_missing_levels() -> None:
    df = pd.DataFrame({
        "id": [
            "missing_nan",
            "missing_none",
            "below_threshold",
            "at_threshold",
            "above_threshold",
        ],
        "level": [float("nan"), None, 1, 2, 3],
    })

    result = _filter_under_community_level(df, community_level=2)

    assert result["id"].to_list() == [
        "missing_nan",
        "missing_none",
        "below_threshold",
        "at_threshold",
    ]
