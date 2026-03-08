# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from unittest.mock import AsyncMock, patch

import graphrag.data_model.schemas as schemas
import pandas as pd
from graphrag.index.operations.summarize_communities.summarize_communities import (
    summarize_communities,
)
from graphrag.index.operations.summarize_communities.typing import (
    CommunityReport,
)


def _make_nodes(levels: list[int]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            schemas.COMMUNITY_ID: i,
            schemas.COMMUNITY_LEVEL: level,
            schemas.TITLE: f"node_{i}",
        }
        for i, level in enumerate(levels)
    ])


def _make_communities(hierarchy: list[tuple[int, int, int]]) -> pd.DataFrame:
    seen: dict[int, dict] = {}
    for community, level, child in hierarchy:
        if community not in seen:
            seen[community] = {
                "community": community,
                "level": level,
                "children": [],
            }
        seen[community]["children"].append(child)
    return pd.DataFrame(list(seen.values()))


def _make_report(community_id: int, level: int) -> CommunityReport:
    return CommunityReport(
        community=community_id,
        title=f"Report for community {community_id}",
        summary=f"Summary {community_id}",
        full_content=f"Full content {community_id}",
        full_content_json="{}",
        rank=1.0,
        level=level,
        rating_explanation="test",
        findings=[],
    )


def _make_local_contexts(communities: list[tuple[int, int]]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            schemas.COMMUNITY_ID: community_id,
            schemas.COMMUNITY_LEVEL: level,
            schemas.CONTEXT_STRING: f"context for {community_id}",
            schemas.CONTEXT_SIZE: 10,
            schemas.CONTEXT_EXCEED_FLAG: False,
            schemas.ALL_CONTEXT: [],
        }
        for community_id, level in communities
    ])


class MockTokenizer:
    def num_tokens(self, text: str) -> int:
        return len(text.split())


async def test_summarize_communities_passes_accumulated_reports():
    nodes = _make_nodes([0, 0, 1, 1])
    communities = _make_communities([(2, 0, 0), (2, 0, 1), (3, 0, 2), (3, 0, 3)])
    local_contexts = _make_local_contexts([(0, 1), (1, 1), (2, 0), (3, 0)])

    report_dfs_received: list[pd.DataFrame] = []
    levels_received: list[int] = []

    def mock_level_context_builder(
        report_df,
        community_hierarchy_df,
        local_context_df,
        level,
        tokenizer,
        max_context_tokens,
    ):
        report_dfs_received.append(report_df.copy())
        levels_received.append(level)
        return local_context_df[local_context_df[schemas.COMMUNITY_LEVEL] == level]

    mock_callbacks = AsyncMock()
    mock_callbacks.progress = None

    with patch(
        "graphrag.index.operations.summarize_communities.summarize_communities.derive_from_rows"
    ) as mock_derive, patch(
        "graphrag.index.operations.summarize_communities.summarize_communities.progress_ticker"
    ) as mock_ticker:
        mock_ticker.return_value = lambda: None

        def side_effect(df, func, **kwargs):
            return [
                _make_report(row[schemas.COMMUNITY_ID], row[schemas.COMMUNITY_LEVEL])
                for _, row in df.iterrows()
            ]

        mock_derive.side_effect = side_effect

        result = await summarize_communities(
            nodes=nodes,
            communities=communities,
            local_contexts=local_contexts,
            level_context_builder=mock_level_context_builder,
            callbacks=mock_callbacks,
            model=AsyncMock(),
            prompt="test prompt",
            tokenizer=MockTokenizer(),
            max_input_length=8000,
            max_report_length=1000,
            num_threads=1,
            async_type="asyncio",
        )

    assert len(levels_received) == 2
    assert levels_received[0] == 1
    assert levels_received[1] == 0

    assert report_dfs_received[0].empty

    assert not report_dfs_received[1].empty
    level_1_community_ids = set(report_dfs_received[1][schemas.COMMUNITY_ID].tolist())
    assert level_1_community_ids == {0, 1}

    assert len(result) == 4
