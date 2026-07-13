# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Model cost registry module."""

from typing import Any, ClassVar, TypedDict, cast

from litellm import model_cost
from typing_extensions import Required, Self


class ModelCosts(TypedDict, total=False):
    """Model costs."""

    input_cost_per_token: Required[float]
    output_cost_per_token: Required[float]
    input_cost_per_token_above_512k_tokens: float
    output_cost_per_token_above_512k_tokens: float
    input_cost_per_token_priority: float
    output_cost_per_token_priority: float
    input_cost_per_token_above_512k_tokens_priority: float
    output_cost_per_token_above_512k_tokens_priority: float
    cache_read_input_token_cost: float
    cache_read_input_token_cost_above_512k_tokens: float
    cache_read_input_token_cost_priority: float
    cache_read_input_token_cost_above_512k_tokens_priority: float
    cache_creation_input_token_cost: float
    max_input_tokens: int
    max_output_tokens: int
    litellm_provider: str
    mode: str
    source: str
    supported_modalities: list[str]
    supports_adaptive_thinking: bool
    supports_function_calling: bool
    supports_multimodal: bool
    supports_prompt_caching: bool
    supports_reasoning: bool
    supports_system_messages: bool
    supports_tool_choice: bool
    supports_video_input: bool
    supports_vision: bool


_MINIMAX_M3_COSTS: ModelCosts = {
    "input_cost_per_token": 0.3 / 1_000_000,
    "output_cost_per_token": 1.2 / 1_000_000,
    "input_cost_per_token_above_512k_tokens": 0.6 / 1_000_000,
    "output_cost_per_token_above_512k_tokens": 2.4 / 1_000_000,
    "input_cost_per_token_priority": 0.45 / 1_000_000,
    "output_cost_per_token_priority": 1.8 / 1_000_000,
    "input_cost_per_token_above_512k_tokens_priority": 0.9 / 1_000_000,
    "output_cost_per_token_above_512k_tokens_priority": 3.6 / 1_000_000,
    "cache_read_input_token_cost": 0.06 / 1_000_000,
    "cache_read_input_token_cost_above_512k_tokens": 0.12 / 1_000_000,
    "cache_read_input_token_cost_priority": 0.09 / 1_000_000,
    "cache_read_input_token_cost_above_512k_tokens_priority": 0.18 / 1_000_000,
    "max_input_tokens": 1_000_000,
    "max_output_tokens": 524_288,
    "mode": "chat",
    "source": "https://platform.minimax.io/docs/guides/pricing-paygo",
    "supported_modalities": ["text", "image", "video"],
    "supports_adaptive_thinking": True,
    "supports_function_calling": True,
    "supports_multimodal": True,
    "supports_prompt_caching": True,
    "supports_reasoning": True,
    "supports_system_messages": True,
    "supports_tool_choice": True,
    "supports_video_input": True,
    "supports_vision": True,
}

_MINIMAX_M27_COSTS: ModelCosts = {
    "input_cost_per_token": 0.3 / 1_000_000,
    "output_cost_per_token": 1.2 / 1_000_000,
    "cache_read_input_token_cost": 0.06 / 1_000_000,
    "cache_creation_input_token_cost": 0.375 / 1_000_000,
    "max_input_tokens": 204_800,
    "max_output_tokens": 204_800,
    "mode": "chat",
    "source": "https://platform.minimax.io/docs/guides/pricing-paygo",
    "supported_modalities": ["text"],
    "supports_function_calling": True,
    "supports_prompt_caching": True,
    "supports_reasoning": True,
    "supports_system_messages": True,
    "supports_tool_choice": True,
}

ADDITIONAL_MODEL_COSTS: dict[str, ModelCosts] = {
    "minimax/MiniMax-M3": cast(
        "ModelCosts", {**_MINIMAX_M3_COSTS, "litellm_provider": "minimax"}
    ),
    "anthropic/MiniMax-M3": cast(
        "ModelCosts", {**_MINIMAX_M3_COSTS, "litellm_provider": "anthropic"}
    ),
    "minimax/MiniMax-M2.7": cast(
        "ModelCosts", {**_MINIMAX_M27_COSTS, "litellm_provider": "minimax"}
    ),
    "anthropic/MiniMax-M2.7": cast(
        "ModelCosts", {**_MINIMAX_M27_COSTS, "litellm_provider": "anthropic"}
    ),
}


def _select_token_cost(
    costs: ModelCosts,
    key: str,
    *,
    prompt_tokens: int,
    service_tier: str | None,
) -> float:
    """Select a token cost using the request size and service tier."""
    cost_map: dict[str, Any] = dict(costs)
    selected_key = key

    threshold_key = f"{key}_above_512k_tokens"
    if prompt_tokens > 512_000 and threshold_key in cost_map:
        selected_key = threshold_key

    priority_key = f"{selected_key}_priority"
    if (
        service_tier is not None
        and service_tier.lower() == "priority"
        and priority_key in cost_map
    ):
        selected_key = priority_key

    return float(cost_map.get(selected_key, cost_map.get(key, 0.0)))


class ModelCostRegistry:
    """Registry for model costs."""

    _instance: ClassVar["Self | None"] = None
    _model_costs: dict[str, ModelCosts]

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        """Create a new instance of ModelCostRegistry if it does not exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._model_costs = cast("dict[str, ModelCosts]", model_cost)
            self._model_costs.update(ADDITIONAL_MODEL_COSTS)
            self._initialized = True

    def register_model_costs(self, model: str, costs: ModelCosts) -> None:
        """Register the cost per unit for a given model.

        Args
        ----
            model: str
                The model id, e.g., "openai/gpt-4o".
            costs: ModelCosts
                The costs associated with the model.
        """
        self._model_costs[model] = costs

    def get_model_costs(self, model: str) -> ModelCosts | None:
        """Retrieve the cost per unit for a given model.

        Args
        ----
            model: str
                The model id, e.g., "openai/gpt-4o".

        Returns
        -------
            ModelCosts | None
                The costs associated with the model, or None if not found.

        """
        return self._model_costs.get(model)

    def calculate_costs(
        self,
        model: str,
        *,
        prompt_tokens: int,
        completion_tokens: int,
        cache_read_input_tokens: int = 0,
        cache_creation_input_tokens: int = 0,
        service_tier: str | None = None,
    ) -> tuple[float, float] | None:
        """Calculate input and output costs for one model response."""
        costs = self.get_model_costs(model)
        if costs is None:
            return None

        prompt_tokens = max(prompt_tokens, 0)
        completion_tokens = max(completion_tokens, 0)
        if model not in ADDITIONAL_MODEL_COSTS:
            return (
                prompt_tokens * costs["input_cost_per_token"],
                completion_tokens * costs["output_cost_per_token"],
            )

        cache_read_input_tokens = min(max(cache_read_input_tokens, 0), prompt_tokens)
        remaining_tokens = prompt_tokens - cache_read_input_tokens
        cache_creation_input_tokens = min(
            max(cache_creation_input_tokens, 0), remaining_tokens
        )
        uncached_input_tokens = remaining_tokens - cache_creation_input_tokens

        input_rate = _select_token_cost(
            costs,
            "input_cost_per_token",
            prompt_tokens=prompt_tokens,
            service_tier=service_tier,
        )
        output_rate = _select_token_cost(
            costs,
            "output_cost_per_token",
            prompt_tokens=prompt_tokens,
            service_tier=service_tier,
        )
        cache_read_rate = _select_token_cost(
            costs,
            "cache_read_input_token_cost",
            prompt_tokens=prompt_tokens,
            service_tier=service_tier,
        )
        cache_creation_rate = _select_token_cost(
            costs,
            "cache_creation_input_token_cost",
            prompt_tokens=prompt_tokens,
            service_tier=service_tier,
        )

        if "cache_read_input_token_cost" not in costs:
            cache_read_rate = input_rate
        if "cache_creation_input_token_cost" not in costs:
            cache_creation_rate = input_rate

        input_cost = (
            uncached_input_tokens * input_rate
            + cache_read_input_tokens * cache_read_rate
            + cache_creation_input_tokens * cache_creation_rate
        )
        output_cost = completion_tokens * output_rate
        return input_cost, output_cost


model_cost_registry = ModelCostRegistry()
