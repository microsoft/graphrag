# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for incremental update merge operations.

Covers _update_and_merge_relationships and orphan-filtering
in the update pipeline, where old finalized data is merged
with delta data from a new indexing run.
"""

import pandas as pd
from graphrag.index.operations.extract_graph.utils import (
    filter_orphan_relationships,
)
from graphrag.index.update.relationships import (
    _update_and_merge_relationships,
)


def _finalized_entity_row(
    title: str,
    entity_id: str = "e1",
    human_readable_id: int = 0,
    entity_type: str = "THING",
    description: str = "desc",
    frequency: int = 1,
    degree: int = 1,
) -> dict:
    """Build a finalized entity row matching ENTITIES_FINAL_COLUMNS shape."""
    return {
        "id": entity_id,
        "human_readable_id": human_readable_id,
        "title": title,
        "type": entity_type,
        "description": description,
        "text_unit_ids": ["tu1"],
        "frequency": frequency,
        "degree": degree,
    }


def _finalized_relationship_row(
    source: str,
    target: str,
    relationship_id: str = "r1",
    human_readable_id: int = 0,
    weight: float = 1.0,
    description: str = "desc",
    combined_degree: int = 2,
) -> dict:
    """Build a finalized relationship row matching RELATIONSHIPS_FINAL_COLUMNS."""
    return {
        "id": relationship_id,
        "human_readable_id": human_readable_id,
        "source": source,
        "target": target,
        "description": description,
        "weight": weight,
        "combined_degree": combined_degree,
        "text_unit_ids": ["tu1"],
    }


class TestUpdateAndMergeRelationships:
    """Tests for _update_and_merge_relationships."""

    def test_merges_old_and_delta(self):
        """Old and delta relationships with distinct pairs both appear."""
        old = pd.DataFrame([
            _finalized_relationship_row("A", "B", relationship_id="r1"),
        ])
        delta = pd.DataFrame([
            _finalized_relationship_row("C", "D", relationship_id="r2"),
        ])
        merged = _update_and_merge_relationships(old, delta)

        pairs = set(zip(merged["source"], merged["target"], strict=True))
        assert ("A", "B") in pairs
        assert ("C", "D") in pairs
        assert len(merged) == 2

    def test_overlapping_pairs_aggregate(self):
        """Same source+target in old and delta get grouped together."""
        old = pd.DataFrame([
            _finalized_relationship_row("A", "B", relationship_id="r1", weight=2.0),
        ])
        delta = pd.DataFrame([
            _finalized_relationship_row("A", "B", relationship_id="r2", weight=4.0),
        ])
        merged = _update_and_merge_relationships(old, delta)

        assert len(merged) == 1
        assert merged.iloc[0]["weight"] == 3.0  # mean of 2.0 and 4.0

    def test_human_readable_ids_incremented(self):
        """Delta human_readable_ids should be offset by old max + 1."""
        old = pd.DataFrame([
            _finalized_relationship_row("A", "B", human_readable_id=5),
        ])
        delta = pd.DataFrame([
            _finalized_relationship_row("C", "D", human_readable_id=0),
        ])
        merged = _update_and_merge_relationships(old, delta)

        ids = set(merged["human_readable_id"])
        assert len(ids) == 2


class TestUpdatePathOrphanFiltering:
    """Tests that orphan relationships are caught in the update path.

    The update pipeline merges old finalized entities with delta
    entities, then merges old finalized relationships with delta
    relationships. Delta relationships from LLM extraction may
    reference hallucinated entity names that don't exist in the
    merged entity set.
    """

    def test_delta_introduces_orphan_source(self):
        """Delta relationship with hallucinated source is filtered out."""
        merged_entities = pd.DataFrame([
            _finalized_entity_row("A", entity_id="e1"),
            _finalized_entity_row("B", entity_id="e2"),
        ])

        old_rels = pd.DataFrame([
            _finalized_relationship_row("A", "B", relationship_id="r1"),
        ])
        delta_rels = pd.DataFrame([
            _finalized_relationship_row("HALLUCINATED", "B", relationship_id="r2"),
        ])
        merged_rels = _update_and_merge_relationships(old_rels, delta_rels)
        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 1
        assert filtered.iloc[0]["source"] == "A"

    def test_delta_introduces_orphan_target(self):
        """Delta relationship with hallucinated target is filtered out."""
        merged_entities = pd.DataFrame([
            _finalized_entity_row("A", entity_id="e1"),
            _finalized_entity_row("B", entity_id="e2"),
        ])

        old_rels = pd.DataFrame([
            _finalized_relationship_row("A", "B", relationship_id="r1"),
        ])
        delta_rels = pd.DataFrame([
            _finalized_relationship_row("A", "HALLUCINATED", relationship_id="r2"),
        ])
        merged_rels = _update_and_merge_relationships(old_rels, delta_rels)
        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 1
        assert filtered.iloc[0]["target"] == "B"

    def test_delta_introduces_orphan_both_endpoints(self):
        """Delta relationship where both endpoints are hallucinated."""
        merged_entities = pd.DataFrame([
            _finalized_entity_row("A", entity_id="e1"),
            _finalized_entity_row("B", entity_id="e2"),
        ])

        old_rels = pd.DataFrame([
            _finalized_relationship_row(
                "A", "B", relationship_id="r0", human_readable_id=0
            ),
        ])
        delta_rels = pd.DataFrame([
            _finalized_relationship_row("GHOST_1", "GHOST_2", relationship_id="r1"),
        ])
        merged_rels = _update_and_merge_relationships(old_rels, delta_rels)
        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 1
        assert filtered.iloc[0]["source"] == "A"
        assert filtered.iloc[0]["target"] == "B"

    def test_all_valid_after_update(self):
        """When all endpoints exist, nothing is filtered."""
        merged_entities = pd.DataFrame([
            _finalized_entity_row("A", entity_id="e1"),
            _finalized_entity_row("B", entity_id="e2"),
            _finalized_entity_row("C", entity_id="e3"),
        ])

        old_rels = pd.DataFrame([
            _finalized_relationship_row("A", "B", relationship_id="r1"),
        ])
        delta_rels = pd.DataFrame([
            _finalized_relationship_row("B", "C", relationship_id="r2"),
        ])
        merged_rels = _update_and_merge_relationships(old_rels, delta_rels)
        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        assert len(filtered) == 2

    def test_old_relationship_becomes_orphan_after_entity_merge(self):
        """Edge case: entity removed in delta makes old relationship orphan.

        This can happen if entity resolution during merge drops an
        entity that was previously referenced by a relationship.
        """
        merged_entities = pd.DataFrame([
            _finalized_entity_row("A", entity_id="e1"),
            _finalized_entity_row("B", entity_id="e2"),
        ])

        old_rels = pd.DataFrame([
            _finalized_relationship_row(
                "A", "REMOVED", relationship_id="r1", human_readable_id=0
            ),
            _finalized_relationship_row(
                "A", "B", relationship_id="r2", human_readable_id=1
            ),
        ])
        delta_rels = pd.DataFrame([
            _finalized_relationship_row(
                "B", "A", relationship_id="r3", human_readable_id=0
            ),
        ])
        merged_rels = _update_and_merge_relationships(old_rels, delta_rels)
        filtered = filter_orphan_relationships(merged_rels, merged_entities)

        surviving_pairs = set(zip(filtered["source"], filtered["target"], strict=True))
        assert ("A", "REMOVED") not in surviving_pairs
        assert len(filtered) >= 1
