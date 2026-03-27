# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.data_model.community import Community
from graphrag.data_model.community_report import CommunityReport
from graphrag.query.context_builder.local_experiment_selector import (
    is_leaf,
    select_flat_ranked,
    select_leaf_only,
    select_leaf_then_parent_mix,
    select_pyramid,
    sort_reports_by_priority,
)


class DummyTokenizer:
    def num_tokens(self, text: str) -> int:
        return len(text.split())


def _community(
    community_id: str,
    parent: str = "",
    children: list[str] | None = None,
) -> Community:
    return Community(
        id=community_id,
        short_id=community_id,
        title=f"community-{community_id}",
        level="1",
        parent=parent,
        children=children or [],
    )


def _report(community_id: str, rank: float = 1.0) -> CommunityReport:
    return CommunityReport(
        id=f"r-{community_id}",
        short_id=community_id,
        title=f"report-{community_id}",
        community_id=community_id,
        summary=f"summary {community_id}",
        full_content=f"full {community_id}",
        rank=rank,
    )


def test_is_leaf():
    assert is_leaf(_community("1")) is True
    assert is_leaf(_community("2", children=["3"])) is False


def test_policy_leaf_only_selection():
    communities = {
        "p": _community("p", children=["l1", "l2"]),
        "l1": _community("l1", parent="p"),
        "l2": _community("l2", parent="p"),
    }
    matches = {"p": 3, "l1": 3, "l2": 2}
    ranked = sort_reports_by_priority(
        [_report("p", 9), _report("l1", 8), _report("l2", 7)], matches
    )

    result = select_leaf_only(ranked, communities, DummyTokenizer(), token_budget=20)

    assert [report.community_id for report in result.selected_reports][:2] == [
        "l1",
        "l2",
    ]


def test_policy_leaf_then_parent_mix_replacement_and_warning():
    communities = {
        "p": _community("p", children=["l1", "l2"]),
        "l1": _community("l1", parent="p"),
        "l2": _community("l2", parent="p"),
    }
    ranked = [_report("l1", 10), _report("l2", 9), _report("p", 8)]

    result = select_leaf_then_parent_mix(ranked, communities, DummyTokenizer(), 6)
    selected_ids = [report.community_id for report in result.selected_reports]

    assert "p" in selected_ids
    assert len(selected_ids) == len(set(selected_ids))

    warn_result = select_leaf_then_parent_mix([_report("l1", 10)], communities, DummyTokenizer(), 10)
    assert warn_result.warnings


def test_policy_pyramid_ordering():
    communities = {
        "gp": _community("gp", children=["p"]),
        "p": _community("p", parent="gp", children=["l1"]),
        "l1": _community("l1", parent="p"),
    }
    ranked = [_report("l1", 10), _report("p", 8), _report("gp", 7)]

    result = select_pyramid(ranked, communities, DummyTokenizer(), token_budget=20)
    selected_ids = [report.community_id for report in result.selected_reports]

    assert selected_ids[0] == "l1"
    assert "p" in selected_ids


def test_policy_flat_ranked():
    ranked = [_report("1", 1), _report("2", 2), _report("3", 3)]

    result = select_flat_ranked(ranked, DummyTokenizer(), token_budget=20)

    assert [report.community_id for report in result.selected_reports] == ["1", "2", "3"]
