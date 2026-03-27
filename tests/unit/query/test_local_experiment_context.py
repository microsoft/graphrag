# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import logging

import pandas as pd
from graphrag.data_model.community import Community
from graphrag.data_model.community_report import CommunityReport
from graphrag.data_model.covariate import Covariate
from graphrag.data_model.entity import Entity
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
    ConversationRole,
)
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch


class DummyTokenizer:
    def encode(self, text: str) -> list[int]:
        return [1] * len(text.split())

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(["x"] * len(token_ids))

    def num_tokens(self, text: str) -> int:
        return len(self.encode(text))


def _builder() -> LocalSearchMixedContext:
    entity = Entity(id="e1", short_id="e1", title="Entity 1", community_ids=["l1"])
    communities = [
        Community(id="p1", short_id="p1", title="P1", level="1", parent="", children=["l1"]),
        Community(id="l1", short_id="l1", title="L1", level="2", parent="p1", children=[]),
    ]
    reports = [
        CommunityReport(
            id="r-p1",
            short_id="p1",
            title="Parent",
            community_id="p1",
            summary="parent summary",
            full_content="PARENT FULL CONTENT",
            rank=5,
        ),
        CommunityReport(
            id="r-l1",
            short_id="l1",
            title="Leaf",
            community_id="l1",
            summary="leaf summary",
            full_content="LEAF FULL CONTENT",
            rank=10,
        ),
    ]
    claims = [
        Covariate(
            id="c1",
            short_id="c1",
            subject_id="e1",
            covariate_type="claim",
            attributes={"description": "claim-one"},
        )
    ]
    return LocalSearchMixedContext(
        entities=[entity],
        communities=communities,
        community_reports=reports,
        relationships=[],
        text_units=[],
        covariates={"claims": claims},
        entity_text_embeddings=object(),  # type: ignore[arg-type]
        text_embedder=object(),  # type: ignore[arg-type]
        tokenizer=DummyTokenizer(),  # type: ignore[arg-type]
    )


def _history() -> ConversationHistory:
    history = ConversationHistory()
    history.add_turn(ConversationRole.USER, "u1")
    history.add_turn(ConversationRole.ASSISTANT, "a1")
    history.add_turn(ConversationRole.USER, "u2")
    history.add_turn(ConversationRole.ASSISTANT, "a2")
    history.add_turn(ConversationRole.USER, "u3")
    history.add_turn(ConversationRole.ASSISTANT, "a3")
    history.add_turn(ConversationRole.USER, "u4")
    history.add_turn(ConversationRole.ASSISTANT, "a4")
    return history


def test_history_and_covariate_switch(monkeypatch):
    builder = _builder()
    monkeypatch.setattr(
        "graphrag.query.structured_search.local_search.mixed_context.map_query_to_entities",
        lambda **_: [next(iter(builder.entities.values()))],
    )

    history = _history()
    result_off = builder.build_context(
        query="q",
        conversation_history=history,
        experiment_enabled=True,
        experiment_history_enabled=False,
        experiment_covariate_enabled=False,
        prompt_logging_enabled=True,
    )
    result_on = builder.build_context(
        query="q",
        conversation_history=history,
        experiment_enabled=True,
        experiment_history_enabled=True,
        experiment_covariate_enabled=True,
        experiment_history_max_turns=3,
        prompt_logging_enabled=True,
    )

    assert "conversation history" not in result_off.context_chunks.lower()
    assert "conversation history" in result_on.context_chunks.lower()
    assert "claims" not in result_off.context_records
    assert "claims" in result_on.context_records


def test_summary_only_context_excludes_full_content_and_local_tables(monkeypatch):
    builder = _builder()
    monkeypatch.setattr(
        "graphrag.query.structured_search.local_search.mixed_context.map_query_to_entities",
        lambda **_: [next(iter(builder.entities.values()))],
    )

    result = builder.build_context(
        query="q",
        experiment_enabled=True,
        community_selection_policy="leaf_only",
        prompt_logging_enabled=True,
    )

    assert "LEAF FULL CONTENT" not in result.context_chunks
    assert "PARENT FULL CONTENT" not in result.context_chunks
    assert "entities" not in result.context_records
    assert "relationships" not in result.context_records
    assert "sources" not in result.context_records


def test_prompt_logging_payload_generation(caplog):
    search = LocalSearch(
        model=object(),  # type: ignore[arg-type]
        context_builder=object(),  # type: ignore[arg-type]
        tokenizer=DummyTokenizer(),  # type: ignore[arg-type]
    )
    context_records = {
        "experiment_meta": pd.DataFrame([
            {
                "experiment_condition_id": "leaf_only:h1:c1",
                "selection_policy": "leaf_only",
                "history_enabled": True,
                "covariate_enabled": True,
                "selected_community_ids": "l1,p1",
                "selected_community_titles": "Leaf,Parent",
                "warnings": "warn",
                "prompt_logging_enabled": True,
            }
        ])
    }

    with caplog.at_level(logging.INFO):
        search._log_final_prompt_payload(context_records, "hello", "system prompt")

    assert "local_search_prompt_payload" in caplog.text
