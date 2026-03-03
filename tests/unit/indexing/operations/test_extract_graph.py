# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for extract_graph merge and orphan-filtering operations.

Validates that _merge_entities, _merge_relationships, and
filter_orphan_relationships correctly aggregate per-text-unit
extraction results and remove relationships whose source or
target has no corresponding entity.
"""

import pandas as pd
from graphrag.index.operations.extract_graph.extract_graph import (
    _merge_entities,
    _merge_relationships,
)
from graphrag.index.operations.extract_graph.utils import (
    filter_orphan_relationships,
)


def _entity_row(
    title: str,
    entity_type: str = "THING",
    description: str = "desc",
    source_id: str = "tu1",
) -> dict:
    """Build a single raw entity row as produced by the graph extractor."""
    return {
        "title": title,
        "type": entity_type,
        "description": description,
        "source_id": source_id,
    }


def _relationship_row(
    source: str,
    target: str,
    weight: float = 1.0,
    description: str = "desc",
    source_id: str = "tu1",
) -> dict:
    """Build a single raw relationship row as produced by the graph extractor."""
    return {
        "source": source,
        "target": target,
        "weight": weight,
        "description": description,
        "source_id": source_id,
    }


class TestMergeEntities:
    """Tests for the _merge_entities aggregation helper."""

    def test_groups_by_title_and_type(self):
        """Entities with the same title+type merge into one row."""
        df1 = pd.DataFrame([_entity_row("A", "PERSON")])
        df2 = pd.DataFrame([_entity_row("A", "PERSON", source_id="tu2")])
        merged = _merge_entities([df1, df2])

        assert len(merged) == 1
        assert merged.iloc[0]["title"] == "A"
        assert merged.iloc[0]["frequency"] == 2

    def test_different_types_stay_separate(self):
        """Same title but different type should not merge."""
        df = pd.DataFrame([
            _entity_row("A", "PERSON"),
            _entity_row("A", "ORG"),
        ])
        merged = _merge_entities([df])

        assert len(merged) == 2

    def test_empty_input(self):
        """Empty entity list should produce an empty DataFrame."""
        df = pd.DataFrame(columns=["title", "type", "description", "source_id"])
        merged = _merge_entities([df])

        assert len(merged) == 0


class TestMergeRelationships:
    """Tests for the _merge_relationships aggregation helper."""

    def test_groups_by_source_target(self):
        """Relationships with same source+target merge and sum weight."""
        df1 = pd.DataFrame([_relationship_row("A", "B", weight=2.0)])
        df2 = pd.DataFrame([_relationship_row("A", "B", weight=3.0)])
        merged = _merge_relationships([df1, df2])

        assert len(merged) == 1
        assert merged.iloc[0]["weight"] == 5.0

    def test_distinct_pairs_stay_separate(self):
        """Different source-target pairs remain separate rows."""
        df = pd.DataFrame([
            _relationship_row("A", "B"),
            _relationship_row("B", "C"),
        ])
        merged = _merge_relationships([df])

        assert len(merged) == 2

    def test_empty_input(self):
        """Empty relationship list should produce an empty DataFrame."""
        df = pd.DataFrame(
            columns=["source", "target", "weight", "description", "source_id"]
        )
        merged = _merge_relationships([df])

        assert len(merged) == 0


class TestFilterOrphanRelationships:
    """Tests for orphan relationship filtering.

    After LLM graph extraction, relationships may reference entity
    names that have no corresponding entity row. These must be
    removed before downstream processing.
    """

    def test_all_valid_relationships_kept(self):
        """Relationships whose endpoints all exist should be retained."""
        entities = pd.DataFrame([
            _entity_row("A"),
            _entity_row("B"),
            _entity_row("C"),
        ])
        merged_entities = _merge_entities([entities])

        relationships = pd.DataFrame([
            _relationship_row("A", "B"),
            _relationship_row("B", "C"),
        ])
        merged_rels = _merge_relationships([relationships])

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 2

    def test_removes_relationship_with_missing_source(self):
        """Relationship whose source has no entity entry is dropped."""
        entities = pd.DataFrame([_entity_row("B")])
        merged_entities = _merge_entities([entities])

        relationships = pd.DataFrame([
            _relationship_row("PHANTOM", "B"),
        ])
        merged_rels = _merge_relationships([relationships])

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 0

    def test_removes_relationship_with_missing_target(self):
        """Relationship whose target has no entity entry is dropped."""
        entities = pd.DataFrame([_entity_row("A")])
        merged_entities = _merge_entities([entities])

        relationships = pd.DataFrame([
            _relationship_row("A", "PHANTOM"),
        ])
        merged_rels = _merge_relationships([relationships])

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 0

    def test_removes_relationship_with_both_missing(self):
        """Relationship where both endpoints are missing is dropped."""
        entities = pd.DataFrame([_entity_row("A")])
        merged_entities = _merge_entities([entities])

        relationships = pd.DataFrame([
            _relationship_row("GHOST_1", "GHOST_2"),
        ])
        merged_rels = _merge_relationships([relationships])

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 0

    def test_keeps_valid_drops_orphan_mixed(self):
        """Valid and orphaned relationships coexist; only valid survive."""
        entities = pd.DataFrame([
            _entity_row("A"),
            _entity_row("B"),
        ])
        merged_entities = _merge_entities([entities])

        relationships = pd.DataFrame([
            _relationship_row("A", "B"),
            _relationship_row("A", "PHANTOM"),
            _relationship_row("PHANTOM", "B"),
            _relationship_row("GHOST_1", "GHOST_2"),
        ])
        merged_rels = _merge_relationships([relationships])

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 1
        assert filtered.iloc[0]["source"] == "A"
        assert filtered.iloc[0]["target"] == "B"

    def test_empty_entities_drops_all_relationships(self):
        """If there are no entities, all relationships are orphaned."""
        entities = pd.DataFrame(columns=["title", "type", "description", "source_id"])
        merged_entities = _merge_entities([entities])

        relationships = pd.DataFrame([
            _relationship_row("A", "B"),
        ])
        merged_rels = _merge_relationships([relationships])

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 0

    def test_empty_relationships_returns_empty(self):
        """If there are no relationships, result is empty DataFrame."""
        entities = pd.DataFrame([_entity_row("A")])
        merged_entities = _merge_entities([entities])

        relationships = pd.DataFrame(
            columns=["source", "target", "weight", "description", "source_id"]
        )
        merged_rels = _merge_relationships([relationships])

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 0

    def test_preserves_all_columns(self):
        """Filtered DataFrame retains all original columns."""
        entities = pd.DataFrame([
            _entity_row("A"),
            _entity_row("B"),
        ])
        merged_entities = _merge_entities([entities])

        relationships = pd.DataFrame([
            _relationship_row("A", "B", weight=5.0, description="linked"),
        ])
        merged_rels = _merge_relationships([relationships])

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert set(filtered.columns) == set(merged_rels.columns)
        assert filtered.iloc[0]["weight"] == 5.0
        assert filtered.iloc[0]["description"] == ["linked"]

    def test_multi_text_unit_orphan(self):
        """Orphan detected across multiple text units after merge."""
        df1 = pd.DataFrame([
            _entity_row("A", source_id="tu1"),
            _relationship_row("A", "HALLUCINATED", source_id="tu1"),
        ])
        df2 = pd.DataFrame([
            _entity_row("A", source_id="tu2"),
            _relationship_row("A", "HALLUCINATED", source_id="tu2"),
        ])

        entity_dfs = [
            df1[["title", "type", "description", "source_id"]],
            df2[["title", "type", "description", "source_id"]],
        ]
        rel_dfs = [
            df1[["source", "target", "weight", "description", "source_id"]],
            df2[["source", "target", "weight", "description", "source_id"]],
        ]

        merged_entities = _merge_entities(entity_dfs)
        merged_rels = _merge_relationships(rel_dfs)

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 0

    def test_resets_index_after_filter(self):
        """Filtered DataFrame should have a clean 0-based index."""
        entities = pd.DataFrame([
            _entity_row("A"),
            _entity_row("B"),
            _entity_row("C"),
        ])
        merged_entities = _merge_entities([entities])

        relationships = pd.DataFrame([
            _relationship_row("PHANTOM", "B"),
            _relationship_row("A", "B"),
            _relationship_row("A", "PHANTOM"),
            _relationship_row("B", "C"),
        ])
        merged_rels = _merge_relationships([relationships])

        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert list(filtered.index) == list(range(len(filtered)))
