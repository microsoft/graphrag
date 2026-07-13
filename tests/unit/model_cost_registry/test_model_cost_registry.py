# Copyright (c) 2026 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for the model cost registry."""

import pytest
from graphrag_llm.config import ModelConfig
from graphrag_llm.metrics.default_metrics_processor import DefaultMetricsProcessor
from graphrag_llm.model_cost_registry import model_cost_registry
from graphrag_llm.types import LLMCompletionResponse


@pytest.mark.parametrize("provider", ["minimax", "anthropic"])
@pytest.mark.parametrize(
    ("model", "max_input_tokens", "modalities", "adaptive_thinking"),
    [
        ("MiniMax-M3", 1_000_000, ["text", "image", "video"], True),
        ("MiniMax-M2.7", 204_800, ["text"], False),
    ],
)
def test_minimax_model_costs_registered_for_supported_protocols(
    provider: str,
    model: str,
    max_input_tokens: int,
    modalities: list[str],
    adaptive_thinking: bool,
) -> None:
    """Ensure each model and protocol alias resolves to the target metadata."""
    costs = model_cost_registry.get_model_costs(f"{provider}/{model}")

    assert costs is not None
    assert costs.get("max_input_tokens") == max_input_tokens
    assert costs["input_cost_per_token"] == 0.3 / 1_000_000
    assert costs["output_cost_per_token"] == 1.2 / 1_000_000
    assert costs.get("supported_modalities") == modalities
    assert costs.get("supports_adaptive_thinking", False) is adaptive_thinking
    assert costs.get("supports_reasoning") is True


@pytest.mark.parametrize(
    ("prompt_tokens", "service_tier", "expected_input", "expected_output"),
    [
        (512_000, None, 0.1296, 0.0012),
        (600_000, None, 0.312, 0.0024),
        (512_000, "priority", 0.1944, 0.0018),
        (600_000, "priority", 0.468, 0.0036),
    ],
)
def test_minimax_m3_pricing_tiers(
    prompt_tokens: int,
    service_tier: str | None,
    expected_input: float,
    expected_output: float,
) -> None:
    """Apply each context-length and service-tier rate, including cache reads."""
    costs = model_cost_registry.calculate_costs(
        "minimax/MiniMax-M3",
        prompt_tokens=prompt_tokens,
        completion_tokens=1_000,
        cache_read_input_tokens=100_000,
        service_tier=service_tier,
    )

    assert costs is not None
    input_cost, output_cost = costs
    assert input_cost == pytest.approx(expected_input)
    assert output_cost == pytest.approx(expected_output)


def test_minimax_m27_cache_read_and_creation_costs() -> None:
    """Apply the separate cache-read and cache-creation rates for M2.7."""
    costs = model_cost_registry.calculate_costs(
        "minimax/MiniMax-M2.7",
        prompt_tokens=1_000,
        completion_tokens=100,
        cache_read_input_tokens=200,
        cache_creation_input_tokens=300,
    )

    assert costs is not None
    input_cost, output_cost = costs
    assert input_cost == pytest.approx(0.0002745)
    assert output_cost == pytest.approx(0.00012)


def test_default_metrics_processor_uses_service_tier_and_cached_tokens() -> None:
    """Calculate response metrics from actual usage details and service tier."""
    response = LLMCompletionResponse.model_validate({
        "id": "response-id",
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "logprobs": None,
                "message": {"content": "Done.", "role": "assistant"},
            }
        ],
        "created": 0,
        "model": "MiniMax-M3",
        "object": "chat.completion",
        "service_tier": "priority",
        "usage": {
            "completion_tokens": 1_000,
            "prompt_tokens": 600_000,
            "total_tokens": 601_000,
            "prompt_tokens_details": {"cached_tokens": 100_000},
        },
    })
    metrics: dict[str, float] = {}

    DefaultMetricsProcessor().process_metrics(
        model_config=ModelConfig(
            model_provider="minimax",
            model="MiniMax-M3",
            api_key="test-key",
        ),
        metrics=metrics,
        input_args={},
        response=response,
    )

    assert metrics["input_cost"] == pytest.approx(0.468)
    assert metrics["output_cost"] == pytest.approx(0.0036)
    assert metrics["total_cost"] == pytest.approx(0.4716)
