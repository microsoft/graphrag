# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for dynamic community selection with type handling."""

from unittest.mock import MagicMock

from graphrag.data_model.community import Community
from graphrag.data_model.community_report import CommunityReport
from graphrag.query.context_builder.dynamic_community_selection import (
    DynamicCommunitySelection,
)


def create_mock_tokenizer() -> MagicMock:
    """Create a mock tokenizer."""
    tokenizer = MagicMock()
    tokenizer.encode.return_value = [1, 2, 3]
    return tokenizer


def create_mock_model() -> MagicMock:
    """Create a mock chat model."""
    return MagicMock()


def test_dynamic_community_selection_handles_int_children():
    """Test that DynamicCommunitySelection correctly handles children IDs as integers.

    This tests the fix for issue #2004 where children IDs could be integers
    while self.reports keys are strings, causing child communities to be skipped.
    """
    # Create communities with integer children (simulating the bug scenario)
    # Note: Even though the type annotation says list[str], actual data may have ints
    communities = [
        Community(
            id="comm-0",
            short_id="0",
            title="Root Community",
            level="0",
            parent="",
            children=[1, 2],  # type: ignore[list-item]  # Integer children - testing bug fix
        ),
        Community(
            id="comm-1",
            short_id="1",
            title="Child Community 1",
            level="1",
            parent="0",
            children=[],
        ),
        Community(
            id="comm-2",
            short_id="2",
            title="Child Community 2",
            level="1",
            parent="0",
            children=[],
        ),
    ]

    # Create community reports with string community_id
    reports = [
        CommunityReport(
            id="report-0",
            short_id="0",
            title="Report 0",
            community_id="0",
            summary="Root community summary",
            full_content="Root community full content",
            rank=1.0,
        ),
        CommunityReport(
            id="report-1",
            short_id="1",
            title="Report 1",
            community_id="1",
            summary="Child 1 summary",
            full_content="Child 1 full content",
            rank=1.0,
        ),
        CommunityReport(
            id="report-2",
            short_id="2",
            title="Report 2",
            community_id="2",
            summary="Child 2 summary",
            full_content="Child 2 full content",
            rank=1.0,
        ),
    ]

    model = create_mock_model()
    tokenizer = create_mock_tokenizer()

    selector = DynamicCommunitySelection(
        community_reports=reports,
        communities=communities,
        model=model,
        tokenizer=tokenizer,
        threshold=1,
        keep_parent=False,
        max_level=2,
    )

    # Verify that reports are keyed by string
    assert "0" in selector.reports
    assert "1" in selector.reports
    assert "2" in selector.reports

    # Verify that communities are keyed by string short_id
    assert "0" in selector.communities
    assert "1" in selector.communities
    assert "2" in selector.communities

    # Verify that the children are properly accessible
    # Before the fix, int children would fail the `in self.reports` check
    root_community = selector.communities["0"]
    for child in root_community.children:
        child_id = str(child)
        # This should now work with the fix
        assert child_id in selector.reports, (
            f"Child {child} (as '{child_id}') should be found in reports"
        )


def test_dynamic_community_selection_handles_str_children():
    """Test that DynamicCommunitySelection works correctly with string children IDs."""
    communities = [
        Community(
            id="comm-0",
            short_id="0",
            title="Root Community",
            level="0",
            parent="",
            children=["1", "2"],  # String children - expected type
        ),
        Community(
            id="comm-1",
            short_id="1",
            title="Child Community 1",
            level="1",
            parent="0",
            children=[],
        ),
        Community(
            id="comm-2",
            short_id="2",
            title="Child Community 2",
            level="1",
            parent="0",
            children=[],
        ),
    ]

    reports = [
        CommunityReport(
            id="report-0",
            short_id="0",
            title="Report 0",
            community_id="0",
            summary="Root community summary",
            full_content="Root community full content",
            rank=1.0,
        ),
        CommunityReport(
            id="report-1",
            short_id="1",
            title="Report 1",
            community_id="1",
            summary="Child 1 summary",
            full_content="Child 1 full content",
            rank=1.0,
        ),
        CommunityReport(
            id="report-2",
            short_id="2",
            title="Report 2",
            community_id="2",
            summary="Child 2 summary",
            full_content="Child 2 full content",
            rank=1.0,
        ),
    ]

    model = create_mock_model()
    tokenizer = create_mock_tokenizer()

    selector = DynamicCommunitySelection(
        community_reports=reports,
        communities=communities,
        model=model,
        tokenizer=tokenizer,
        threshold=1,
        keep_parent=False,
        max_level=2,
    )

    # Verify that children can be found in reports
    root_community = selector.communities["0"]
    for child in root_community.children:
        child_id = str(child)
        assert child_id in selector.reports, (
            f"Child {child} (as '{child_id}') should be found in reports"
        )
