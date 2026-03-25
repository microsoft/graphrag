# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

import asyncio
import json
from pathlib import Path

from graphrag.index.operations.summarize_communities.summarize_communities import (
    run_extractor,
)
from graphrag.prompts.index.community_report_text_units import COMMUNITY_REPORT_TEXT_PROMPT
from graphrag_llm.completion import create_completion
from graphrag_llm.config import LLMProviderType, ModelConfig


def test_temporal_community_summary_generated_from_sample_file():
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "temporal_conversation_sample.json"
    )
    sample = json.loads(fixture_path.read_text(encoding="utf-8"))
    conversation_text = "\n".join(
        f"[{m['timestamp']}] {m['role']}: {m['content']}" for m in sample["messages"]
    )

    mock_response = json.dumps(
        {
            "title": "배송 상태 커뮤니티 요약",
            "summary": "초기 준비중 상태에서 최신 출고 완료 상태로 전환되었다.",
            "current_state": "현재 상태는 출고 완료이다.",
            "timeline_events": [
                {"summary": "초기 상태", "explanation": "09:01 기준 준비중"},
                {"summary": "최신 업데이트", "explanation": "10:10 기준 출고 완료"},
            ],
            "superseded_facts": [
                {"summary": "준비중 상태", "explanation": "출고 완료로 대체됨"}
            ],
            "date_range": ["2026-01-03", "2026-01-04"],
            "findings": [
                {
                    "summary": "상태 전이 확인",
                    "explanation": "대화 시간 흐름에 따라 배송 상태가 변경되었다.",
                }
            ],
            "rating": 5.0,
            "rating_explanation": "시간 흐름 기반 상태 변화가 명확하다.",
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
            max_report_length=300,
        )
    )

    assert report is not None
    assert "Current State" in report["full_content"]
    assert "Timeline" in report["full_content"]
    assert "Superseded Facts" in report["full_content"]
    assert "Date Range" in report["full_content"]
    assert report["current_state"] == "현재 상태는 출고 완료이다."
    assert report["timeline_events"][1]["summary"] == "최신 업데이트"
    assert report["date_range"] == ["2026-01-03", "2026-01-04"]
    full_content_json = json.loads(report["full_content_json"])
    assert full_content_json["date_range"] == ["2026-01-03", "2026-01-04"]
