# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.data_model.entity import Entity
from graphrag.data_model.relationship import Relationship
from graphrag.data_model.text_unit import TextUnit
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)


class DummyTokenizer:
    def encode(self, text: str) -> list[int]:
        return [1] * len(text.split())

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(["x"] * len(token_ids))

    def num_tokens(self, text: str) -> int:
        return len(self.encode(text))


def _create_context_builder() -> LocalSearchMixedContext:
    return LocalSearchMixedContext(
        entities=[Entity(id="e1", short_id="1", title="A")],
        entity_text_embeddings=object(),  # type: ignore[arg-type]
        text_embedder=object(),  # type: ignore[arg-type]
        text_units=[],
        community_reports=[],
        relationships=[],
        covariates={},
        tokenizer=DummyTokenizer(),  # type: ignore[arg-type]
    )


def test_split_current_and_history_uses_end_turn_index():
    builder = _create_context_builder()
    units = [
        TextUnit(
            id="tu1",
            short_id="1",
            text="old",
            attributes={"end_turn_index": 1, "start_turn_index": 1},
        ),
        TextUnit(
            id="tu2",
            short_id="2",
            text="new",
            attributes={"end_turn_index": 2, "start_turn_index": 2},
        ),
    ]

    current, history = builder._split_current_and_history(units)

    assert [u.id for u in current] == ["tu2"]
    assert [u.id for u in history] == ["tu1"]


def test_sort_text_units_by_temporal_fields():
    builder = _create_context_builder()
    units = [
        TextUnit(
            id="tu2",
            short_id="2",
            text="second",
            attributes={"start_turn_index": 2, "chunk_index_in_conversation": 2},
        ),
        TextUnit(
            id="tu1",
            short_id="1",
            text="first",
            attributes={"start_turn_index": 1, "chunk_index_in_conversation": 1},
        ),
    ]

    sorted_units = builder._sort_text_units_by_temporal(units)

    assert [u.id for u in sorted_units] == ["tu1", "tu2"]


def test_build_text_unit_context_candidate_marks_in_context_across_current_and_history():
    entity = Entity(id="e1", short_id="1", title="A", text_unit_ids=["tu1", "tu2"])
    context_builder = LocalSearchMixedContext(
        entities=[entity],
        entity_text_embeddings=object(),  # type: ignore[arg-type]
        text_embedder=object(),  # type: ignore[arg-type]
        text_units=[
            TextUnit(
                id="tu1",
                short_id="1",
                text="old",
                attributes={"start_turn_index": 1, "end_turn_index": 1},
            ),
            TextUnit(
                id="tu2",
                short_id="2",
                text="new",
                attributes={"start_turn_index": 2, "end_turn_index": 2},
            ),
        ],
        community_reports=[],
        relationships=[
            Relationship(
                id="r1",
                short_id="1",
                source="A",
                target="B",
                text_unit_ids=["tu1", "tu2"],
            )
        ],
        covariates={},
        tokenizer=DummyTokenizer(),  # type: ignore[arg-type]
    )

    _, context_data = context_builder._build_text_unit_context(
        selected_entities=[entity],
        return_candidate_context=True,
        max_context_tokens=1000,
    )

    assert "sources" in context_data
    assert context_data["sources"]["in_context"].tolist() == [True, True]
