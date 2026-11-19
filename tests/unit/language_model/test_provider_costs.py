# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Cost metrics must distinguish missing pricing from known zero pricing."""

import pytest
from graphrag_llm.config import AuthMethod, ModelConfig
from graphrag_llm.metrics.default_metrics_processor import DefaultMetricsProcessor
from graphrag_llm.model_cost_registry import model_cost_registry
from graphrag_llm.types import LLMCompletionUsage, LLMEmbeddingUsage, Metrics
from graphrag_llm.utils import create_completion_response, create_embedding_response


@pytest.mark.parametrize("request_type", ["chat", "embedding"])
@pytest.mark.parametrize(
    "costs",
    [
        None,
        {"litellm_provider": "test-provider"},
        {"output_cost_per_token": 0.2},
        {"input_cost_per_token": 0.1},
        {"input_cost_per_token": 0.1, "output_cost_per_token": 0.2},
        {"input_cost_per_token": 0.0, "output_cost_per_token": 0.0},
    ],
)
def test_missing_and_known_pricing(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    request_type: str,
    costs,
) -> None:
    monkeypatch.setattr(model_cost_registry, "get_model_costs", lambda _: costs)
    if request_type == "chat":
        response = create_completion_response("hello")
        response.usage = LLMCompletionUsage(
            prompt_tokens=2, completion_tokens=1, total_tokens=3
        )
    else:
        response = create_embedding_response([0.1])
        response.usage = LLMEmbeddingUsage(prompt_tokens=2, total_tokens=2)
    metrics: Metrics = {}
    DefaultMetricsProcessor().process_metrics(
        model_config=ModelConfig(
            model_provider="test-provider",
            model="test-model",
            auth_method=AuthMethod.Provider,
        ),
        metrics=metrics,
        input_args={},
        response=response,
    )
    assert metrics["prompt_tokens"] == 2
    assert metrics["responses_with_tokens"] == 1
    has_pricing = costs is not None and "input_cost_per_token" in costs
    if request_type == "chat":
        has_pricing = (
            has_pricing and costs is not None and "output_cost_per_token" in costs
        )
    if has_pricing:
        assert costs is not None
        expected = 2 * costs["input_cost_per_token"]
        if request_type == "chat":
            expected += costs["output_cost_per_token"]
        assert metrics["total_cost"] == expected
        assert metrics["responses_with_cost"] == 1
        assert "pricing unavailable" not in caplog.text
    else:
        assert "total_cost" not in metrics
        assert "responses_with_cost" not in metrics
        assert "pricing unavailable" in caplog.text
