# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

import asyncio
import json
from pathlib import Path

import pandas as pd

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.data_model.entity import Entity
from graphrag.data_model.relationship import Relationship
from graphrag.data_model.text_unit import TextUnit
from graphrag.index.operations.extract_graph.extract_graph import extract_graph
from graphrag.index.operations.summarize_communities.summarize_communities import (
    run_extractor,
)
from graphrag.index.operations.summarize_descriptions.description_summary_extractor import (
    SummarizeExtractor,
)
from graphrag.prompts.index.community_report_text_units import COMMUNITY_REPORT_TEXT_PROMPT
from graphrag.prompts.index.extract_graph import GRAPH_EXTRACTION_PROMPT
from graphrag.query.structured_search.local_search.mixed_context import LocalSearchMixedContext
from graphrag_llm.completion import create_completion
from graphrag_llm.config import LLMProviderType, ModelConfig


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "temporal_relationship_conversation.json"
)


class _FakeTokenizer:
    def num_tokens(self, text: str) -> int:
        return len(text)


class _FakeSummaryResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeSummaryModel:
    def __init__(self):
        self.tokenizer = _FakeTokenizer()
        self.last_messages = ""

    async def completion_async(self, messages: str):
        self.last_messages = messages
        return _FakeSummaryResponse(content="temporal-summary")


class _FakeVectorStore:
    def search_by_text(self, *args, **kwargs):
        return []


class _FakeEmbedder:
    async def aembed(self, *args, **kwargs):
        return []


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _conversation_text(sample: dict) -> str:
    return "\n".join(
        f"[{m['timestamp']}] {m['role']}: {m['content']}" for m in sample["messages"]
    )


def _text_units_df(sample: dict) -> pd.DataFrame:
    rows = []
    for msg in sample["messages"]:
        rows.append(
            {
                "id": f"tu-{msg['turn_index']}",
                "text": msg["content"],
                "conversation_id": sample["conversation_id"],
                "start_turn_index": msg["turn_index"],
                "end_turn_index": msg["turn_index"],
                "turn_timestamp_start": msg["timestamp"],
                "turn_timestamp_end": msg["timestamp"],
                "included_roles": [msg["role"]],
                "chunk_index_in_conversation": msg["turn_index"] - 1,
                "chunk_index_in_document": 0,
            }
        )
    return pd.DataFrame(rows)


def test_approach1_text_community_report_from_real_conversation_file():
    sample = _load_fixture()
    conversation_text = _conversation_text(sample)

    mock_response = json.dumps(
        {
            "title": "Order-77 배송 상태 커뮤니티",
            "summary": "Order-77는 Carrier Alpha 지연 이후 Carrier Beta 처리로 shipped로 갱신되었다.",
            "current_state": "현재 Order-77 상태는 shipped이며 Payment System이 Carrier Beta 완료를 반영했다.",
            "timeline_events": [
                {"summary": "초기 상태", "explanation": "09:00 Order-77 pending, Carrier Alpha pickup 연결"},
                {"summary": "지연 발생", "explanation": "09:12 Carrier Alpha pickup delay 보고"},
                {"summary": "정정/최신", "explanation": "09:25 Carrier Beta pickup 완료, Order-77 shipped"},
            ],
            "superseded_facts": [
                {"summary": "Carrier Alpha pickup 예정", "explanation": "Carrier Beta 완료 사실로 대체됨"}
            ],
            "date_range": ["2026-02-03", "2026-02-03"],
            "findings": [
                {
                    "summary": "Payment System-Carrier 관계 변경",
                    "explanation": "Payment System이 Carrier Alpha 경로에서 Carrier Beta 완료로 관계 상태를 업데이트했다.",
                }
            ],
            "rating": 7.5,
            "rating_explanation": "정정과 최신 상태 전환이 명확하다.",
        },
        ensure_ascii=False,
    )

    model = create_completion(
        ModelConfig(
            type=LLMProviderType.MockLLM,
            model_provider="openai",
            model="gpt-4o",
            mock_responses=[mock_response],
        )
    )

    report = asyncio.run(
        run_extractor(
            community="1",
            input=conversation_text,
            level=1,
            model=model,
            extraction_prompt=COMMUNITY_REPORT_TEXT_PROMPT,
            max_report_length=400,
        )
    )

    assert report is not None
    assert report["timeline_events"][2]["summary"] == "정정/최신"
    assert "Carrier Beta" in report["current_state"]
    assert "Payment System" in report["findings"][0]["summary"]


def test_approach2_graph_extraction_temporal_and_relationships_from_same_file():
    sample = _load_fixture()
    text_units = _text_units_df(sample)

    mock_outputs = [
        '("entity"<|>ORDER-77<|>EVENT<|>Order-77 pending [time: 09:00] [status: current])##'
        '("entity"<|>PAYMENT SYSTEM<|>ORGANIZATION<|>Payment System tracks order state [time: 09:00])##'
        '("entity"<|>CARRIER ALPHA<|>ORGANIZATION<|>Carrier Alpha pickup link [time: 09:00])##'
        '("relationship"<|>PAYMENT SYSTEM<|>ORDER-77<|>Payment System marks Order-77 pending via Carrier Alpha [time: 09:00] [change: plan]<|>7)<|COMPLETE|>',
        '("entity"<|>CARRIER ALPHA<|>ORGANIZATION<|>Carrier Alpha delay report [time: 09:12] [status: historical])##'
        '("relationship"<|>CARRIER ALPHA<|>ORDER-77<|>Carrier Alpha delayed pickup for Order-77 [time: 09:12] [change: update]<|>8)<|COMPLETE|>',
        '("entity"<|>CARRIER BETA<|>ORGANIZATION<|>Carrier Beta completed pickup [time: 09:25] [status: current])##'
        '("relationship"<|>PAYMENT SYSTEM<|>ORDER-77<|>Payment System corrected Order-77 to shipped via Carrier Beta [time: 09:25] [change: correction]<|>10)<|COMPLETE|>',
    ]

    model = create_completion(
        ModelConfig(
            type=LLMProviderType.MockLLM,
            model_provider="openai",
            model="gpt-4o",
            mock_responses=mock_outputs,
        )
    )

    entities, relationships = asyncio.run(
        extract_graph(
            text_units=text_units,
            callbacks=NoopWorkflowCallbacks(),
            text_column="text",
            id_column="id",
            model=model,
            prompt=GRAPH_EXTRACTION_PROMPT,
            entity_types=["EVENT", "ORGANIZATION"],
            max_gleanings=0,
            num_threads=1,
            async_type=AsyncType.AsyncIO,
        )
    )

    payment_order = relationships[
        (relationships["source"] == "PAYMENT SYSTEM")
        & (relationships["target"] == "ORDER-77")
    ].iloc[0]

    assert any("correction" in item for item in payment_order["description"])
    assert payment_order["first_seen_turn_index"] == 1
    assert payment_order["last_seen_turn_index"] == 3


def test_approach3_local_query_context_splits_current_vs_timeline_from_same_file():
    sample = _load_fixture()

    entities = [
        Entity(
            id="e-order",
            short_id="1",
            title="ORDER-77",
            text_unit_ids=["tu-1", "tu-2", "tu-3"],
        ),
        Entity(
            id="e-pay",
            short_id="2",
            title="PAYMENT SYSTEM",
            text_unit_ids=["tu-1", "tu-3"],
        ),
    ]
    relationships = [
        Relationship(
            id="r1",
            short_id="1",
            source="PAYMENT SYSTEM",
            target="ORDER-77",
            description="pending then shipped",
            text_unit_ids=["tu-1", "tu-3"],
        )
    ]
    text_units = [
        TextUnit(
            id="tu-1",
            short_id="1",
            text=sample["messages"][0]["content"],
            attributes={"start_turn_index": 1, "end_turn_index": 1, "chunk_index_in_conversation": 0},
        ),
        TextUnit(
            id="tu-2",
            short_id="2",
            text=sample["messages"][1]["content"],
            attributes={"start_turn_index": 2, "end_turn_index": 2, "chunk_index_in_conversation": 1},
        ),
        TextUnit(
            id="tu-3",
            short_id="3",
            text=sample["messages"][2]["content"],
            attributes={"start_turn_index": 3, "end_turn_index": 3, "chunk_index_in_conversation": 2},
        ),
    ]

    context_builder = LocalSearchMixedContext(
        entities=entities,
        entity_text_embeddings=_FakeVectorStore(),
        text_embedder=_FakeEmbedder(),
        text_units=text_units,
        relationships=relationships,
        community_reports=[],
        covariates={},
        tokenizer=_FakeTokenizer(),
    )

    context_text, context_data = context_builder._build_text_unit_context(
        selected_entities=entities,
        max_context_tokens=10000,
        return_candidate_context=False,
        column_delimiter="|",
    )

    assert "sources_current" in context_data
    assert "sources_timeline" in context_data
    assert any("Correction" in txt or "shipped" in txt for txt in context_data["sources_current"]["text"].tolist())
    assert any("delay" in txt or "pending" in txt for txt in context_data["sources_timeline"]["text"].tolist())
    assert "Payment System" in context_text or "PAYMENT SYSTEM" in context_text
