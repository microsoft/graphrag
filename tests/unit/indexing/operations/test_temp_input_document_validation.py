# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

import asyncio
from pathlib import Path

import pandas as pd

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.index.operations.extract_graph.extract_graph import extract_graph
from graphrag.prompts.index.extract_graph import GRAPH_EXTRACTION_PROMPT
from graphrag_llm.completion import create_completion
from graphrag_llm.config import LLMProviderType, ModelConfig


DOC_PATH = Path(__file__).resolve().parents[4] / "temp_input" / "order77_timeline_document.md"


def test_temp_input_document_exists_and_supports_temporal_relationship_validation():
    assert DOC_PATH.exists()
    document = DOC_PATH.read_text(encoding="utf-8")

    text_units = pd.DataFrame(
        [
            {
                "id": "doc-tu-1",
                "text": document,
                "conversation_id": "doc-conv",
                "start_turn_index": 1,
                "end_turn_index": 3,
                "turn_timestamp_start": "2026-02-03T09:00:00Z",
                "turn_timestamp_end": "2026-02-03T09:25:00Z",
                "included_roles": ["user", "assistant"],
                "chunk_index_in_conversation": 0,
                "chunk_index_in_document": 0,
            }
        ]
    )

    mock_output = (
        '("entity"<|>ORDER-77<|>EVENT<|>Order-77 transitioned from pending to shipped [time: 09:00->09:25] [status: current])##'
        '("entity"<|>PAYMENT SYSTEM<|>ORGANIZATION<|>Payment System recorded correction and final shipped state [time: 09:25])##'
        '("relationship"<|>PAYMENT SYSTEM<|>ORDER-77<|>Payment System corrected Order-77 state from pending to shipped [change: correction] [order: later]<|>10)<|COMPLETE|>'
    )

    model = create_completion(
        ModelConfig(
            type=LLMProviderType.MockLLM,
            model_provider="openai",
            model="gpt-4o",
            mock_responses=[mock_output],
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

    assert "ORDER-77" in entities["title"].tolist()
    rel = relationships.iloc[0]
    assert rel["source"] == "PAYMENT SYSTEM"
    assert rel["target"] == "ORDER-77"
    assert rel["first_seen_turn_index"] == 1
    assert rel["last_seen_turn_index"] == 3
    assert "correction" in rel["description"][0]
