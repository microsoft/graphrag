# Copyright (C) 2026 Microsoft

"""Tests for the create_communities pure function.

These tests pin down the behavior of the create_communities function
independently of the workflow runner, so that refactoring (vectorizing
the per-level loop, streaming entity reads, streaming writes, etc.)
can be verified against known output.
"""

import uuid

import pandas as pd
import pytest
from graphrag.data_model.schemas import COMMUNITIES_FINAL_COLUMNS
from graphrag.index.workflows.create_communities import create_communities


def _make_title_to_entity_id(
    rows: list[tuple[str, str]],
) -> dict[str, str]:
    """Build a title-to-entity-id mapping from (id, title) pairs."""
    return {title: eid for eid, title in rows}


def _make_relationships(
    rows: list[tuple[str, str, str, float, list[str]]],
) -> pd.DataFrame:
    """Build a minimal relationships DataFrame.

    Each row is (id, source, target, weight, text_unit_ids).
    """
    return pd.DataFrame([
        {
            "id": rid,
            "source": src,
            "target": tgt,
            "weight": w,
            "text_unit_ids": tuids,
            "human_readable_id": i,
        }
        for i, (rid, src, tgt, w, tuids) in enumerate(rows)
    ])


@pytest.fixture
def two_triangles():
    """Two disconnected triangles: {A,B,C} and {D,E,F}."""
    title_to_entity_id = _make_title_to_entity_id([
        ("e1", "A"),
        ("e2", "B"),
        ("e3", "C"),
        ("e4", "D"),
        ("e5", "E"),
        ("e6", "F"),
    ])
    relationships = _make_relationships([
        ("r1", "A", "B", 1.0, ["t1"]),
        ("r2", "A", "C", 1.0, ["t1", "t2"]),
        ("r3", "B", "C", 1.0, ["t2"]),
        ("r4", "D", "E", 1.0, ["t3"]),
        ("r5", "D", "F", 1.0, ["t3", "t4"]),
        ("r6", "E", "F", 1.0, ["t4"]),
    ])
    return title_to_entity_id, relationships


# -------------------------------------------------------------------
# Column schema
# -------------------------------------------------------------------


class TestOutputSchema:
    """Verify the output DataFrame has the expected column schema."""

    def test_has_all_final_columns(self, two_triangles):
        """Output must have exactly the COMMUNITIES_FINAL_COLUMNS."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        assert list(result.columns) == COMMUNITIES_FINAL_COLUMNS

    def test_column_order_matches_schema(self, two_triangles):
        """Column order must match the schema constant exactly."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        for i, col_name in enumerate(COMMUNITIES_FINAL_COLUMNS):
            assert result.columns[i] == col_name


# -------------------------------------------------------------------
# Metadata fields
# -------------------------------------------------------------------


class TestMetadataFields:
    """Verify computed metadata fields like id, title, size, period."""

    def test_uuid_ids(self, two_triangles):
        """Each community id should be a valid UUID4."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        for _, row in result.iterrows():
            parsed = uuid.UUID(row["id"])
            assert parsed.version == 4

    def test_title_format(self, two_triangles):
        """Title should be 'Community N' where N is the community id."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        for _, row in result.iterrows():
            assert row["title"] == f"Community {row['community']}"

    def test_human_readable_id_equals_community(self, two_triangles):
        """human_readable_id should equal the community integer id."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        assert (result["human_readable_id"] == result["community"]).all()

    def test_size_equals_entity_count(self, two_triangles):
        """size should equal the length of entity_ids."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        for _, row in result.iterrows():
            assert row["size"] == len(row["entity_ids"])

    def test_period_is_iso_date(self, two_triangles):
        """period should be a valid ISO date string."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        from datetime import date

        for _, row in result.iterrows():
            date.fromisoformat(row["period"])


# -------------------------------------------------------------------
# Entity aggregation
# -------------------------------------------------------------------


class TestEntityAggregation:
    """Verify that entity_ids are correctly aggregated per community."""

    def test_entity_ids_per_community(self, two_triangles):
        """Each community should contain exactly the entities matching
        its cluster nodes."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        comm_0 = result[result["community"] == 0].iloc[0]
        comm_1 = result[result["community"] == 1].iloc[0]

        assert sorted(comm_0["entity_ids"]) == ["e1", "e2", "e3"]
        assert sorted(comm_1["entity_ids"]) == ["e4", "e5", "e6"]

    def test_entity_ids_are_lists(self, two_triangles):
        """entity_ids should be Python lists, not numpy arrays."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        for _, row in result.iterrows():
            assert isinstance(row["entity_ids"], list)


# -------------------------------------------------------------------
# Relationship and text_unit aggregation
# -------------------------------------------------------------------


class TestRelationshipAggregation:
    """Verify that relationship_ids and text_unit_ids are correctly
    aggregated (intra-community only) and deduplicated."""

    def test_relationship_ids_per_community(self, two_triangles):
        """Each community should only include relationships where both
        endpoints are in the same community."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        comm_0 = result[result["community"] == 0].iloc[0]
        comm_1 = result[result["community"] == 1].iloc[0]

        assert sorted(comm_0["relationship_ids"]) == ["r1", "r2", "r3"]
        assert sorted(comm_1["relationship_ids"]) == ["r4", "r5", "r6"]

    def test_text_unit_ids_per_community(self, two_triangles):
        """text_unit_ids should be the deduplicated union of text units
        from the community's intra-community relationships."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        comm_0 = result[result["community"] == 0].iloc[0]
        comm_1 = result[result["community"] == 1].iloc[0]

        assert sorted(comm_0["text_unit_ids"]) == ["t1", "t2"]
        assert sorted(comm_1["text_unit_ids"]) == ["t3", "t4"]

    def test_lists_are_sorted_and_deduplicated(self, two_triangles):
        """relationship_ids and text_unit_ids should be sorted with
        no duplicates."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        for _, row in result.iterrows():
            assert row["relationship_ids"] == sorted(set(row["relationship_ids"]))
            assert row["text_unit_ids"] == sorted(set(row["text_unit_ids"]))

    def test_cross_community_relationships_excluded(self):
        """A relationship spanning two communities must not appear in
        either community's relationship_ids."""
        title_to_entity_id = _make_title_to_entity_id([
            ("e1", "A"),
            ("e2", "B"),
            ("e3", "C"),
            ("e4", "D"),
            ("e5", "E"),
            ("e6", "F"),
        ])
        relationships = _make_relationships([
            ("r1", "A", "B", 1.0, ["t1"]),
            ("r2", "A", "C", 1.0, ["t1"]),
            ("r3", "B", "C", 1.0, ["t1"]),
            ("r_cross", "C", "D", 0.1, ["t_cross"]),
            ("r4", "D", "E", 1.0, ["t2"]),
            ("r5", "D", "F", 1.0, ["t2"]),
            ("r6", "E", "F", 1.0, ["t2"]),
        ])
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        all_rel_ids = []
        for _, row in result.iterrows():
            all_rel_ids.extend(row["relationship_ids"])
        assert "r_cross" not in all_rel_ids
        assert "t_cross" not in [
            tid for _, row in result.iterrows() for tid in row["text_unit_ids"]
        ]


# -------------------------------------------------------------------
# Parent / children tree
# -------------------------------------------------------------------


class TestParentChildTree:
    """Verify the parent-child tree structure is consistent."""

    def test_level_zero_parent_is_minus_one(self, two_triangles):
        """All level-0 communities should have parent == -1."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        lvl0 = result[result["level"] == 0]
        assert (lvl0["parent"] == -1).all()

    def test_leaf_communities_have_empty_children(self, two_triangles):
        """Communities that are nobody's parent should have children=[]."""
        title_to_entity_id, relationships = two_triangles
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        for _, row in result.iterrows():
            children = row["children"]
            if isinstance(children, list) and len(children) == 0:
                child_rows = result[result["parent"] == row["community"]]
                assert len(child_rows) == 0

    def test_parent_child_bidirectional_consistency_real_data(self):
        """For real test data: if community X lists Y as child,
        then Y's parent must be X."""
        entities_df = pd.read_parquet("tests/verbs/data/entities.parquet")
        title_to_entity_id = dict(
            zip(entities_df["title"], entities_df["id"], strict=False)
        )
        relationships = pd.read_parquet("tests/verbs/data/relationships.parquet")
        result = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=True,
            seed=0xDEADBEEF,
        )
        for _, row in result.iterrows():
            children = row["children"]
            if hasattr(children, "__len__") and len(children) > 0:
                for child_id in children:
                    child_row = result[result["community"] == child_id]
                    assert len(child_row) == 1, (
                        f"Child {child_id} not found or duplicated"
                    )
                    assert child_row.iloc[0]["parent"] == row["community"]


# -------------------------------------------------------------------
# LCC filtering
# -------------------------------------------------------------------


class TestLccFiltering:
    """Verify LCC filtering interaction with create_communities."""

    def test_lcc_reduces_community_count(self):
        """With use_lcc=True and two disconnected components, only the
        larger component's communities should appear."""
        title_to_entity_id = _make_title_to_entity_id([
            ("e1", "A"),
            ("e2", "B"),
            ("e3", "C"),
            ("e4", "D"),
            ("e5", "E"),
            ("e6", "F"),
        ])
        relationships = _make_relationships([
            ("r1", "A", "B", 1.0, ["t1"]),
            ("r2", "A", "C", 1.0, ["t1"]),
            ("r3", "B", "C", 1.0, ["t1"]),
            ("r4", "D", "E", 1.0, ["t2"]),
            ("r5", "D", "F", 1.0, ["t2"]),
            ("r6", "E", "F", 1.0, ["t2"]),
        ])
        result_no_lcc = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=False,
            seed=42,
        )
        result_lcc = create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=True,
            seed=42,
        )
        assert len(result_lcc) < len(result_no_lcc)
        assert len(result_lcc) == 1


# -------------------------------------------------------------------
# Golden file regression (real test data)
# -------------------------------------------------------------------


class TestRealDataRegression:
    """Regression tests using the shared test fixture data.

    These pin exact values so any behavioral change during refactoring
    is caught immediately.
    """

    @pytest.fixture
    def real_result(self) -> pd.DataFrame:
        """Run create_communities on the test fixture data."""
        entities_df = pd.read_parquet("tests/verbs/data/entities.parquet")
        title_to_entity_id = dict(
            zip(entities_df["title"], entities_df["id"], strict=False)
        )
        relationships = pd.read_parquet("tests/verbs/data/relationships.parquet")
        return create_communities(
            title_to_entity_id,
            relationships,
            max_cluster_size=10,
            use_lcc=True,
            seed=0xDEADBEEF,
        )

    def test_row_count(self, real_result: pd.DataFrame):
        """Pin the expected number of communities."""
        assert len(real_result) == 122

    def test_level_distribution(self, real_result: pd.DataFrame):
        """Pin the expected number of communities per level."""
        from collections import Counter

        counts = Counter(real_result["level"].tolist())
        assert counts == {0: 23, 1: 65, 2: 32, 3: 2}

    def test_values_match_golden_file(self, real_result: pd.DataFrame):
        """The output should match the golden Parquet file for all
        columns except id (UUID) and period (date-dependent)."""
        expected = pd.read_parquet("tests/verbs/data/communities.parquet")

        assert len(real_result) == len(expected)

        skip_columns = {"id", "period", "children"}
        for col in COMMUNITIES_FINAL_COLUMNS:
            if col in skip_columns:
                continue
            pd.testing.assert_series_equal(
                real_result[col],
                expected[col],
                check_dtype=False,
                check_index=False,
                check_names=False,
                obj=f"Column '{col}'",
            )

        # children requires special handling: the golden file stores
        # numpy arrays, the function may return lists or arrays
        for i in range(len(real_result)):
            actual_children = list(real_result.iloc[i]["children"])
            expected_children = list(expected.iloc[i]["children"])
            assert actual_children == expected_children, (
                f"Row {i} children mismatch: {actual_children} != {expected_children}"
            )

    def test_communities_with_children(self, real_result: pd.DataFrame):
        """Pin the expected number of communities that have children."""
        has_children = real_result["children"].apply(
            lambda x: hasattr(x, "__len__") and len(x) > 0
        )
        assert has_children.sum() == 24
