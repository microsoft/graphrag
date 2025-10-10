# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utility functions for language models."""

from typing import Any

from graphrag.config.models.language_model_config import LanguageModelConfig


def is_reasoning_model(model: str) -> bool:
    """Return whether the model uses a known OpenAI reasoning model."""
    return model.lower() in {"o1", "o1-mini", "o3-mini"}


def get_openai_model_parameters_from_config(
    config: LanguageModelConfig,
) -> dict[str, Any]:
    """Get the model parameters for a given config, adjusting for reasoning API differences."""
    return get_openai_model_parameters_from_dict(config.model_dump())


def get_openai_model_parameters_from_dict(config: dict[str, Any]) -> dict[str, Any]:
    """Get the model parameters for a given config, adjusting for reasoning API differences."""
    params = {
        "n": config.get("n"),
    }
    if is_reasoning_model(config["model"]):
        params["max_completion_tokens"] = config.get("max_completion_tokens")
        params["reasoning_effort"] = config.get("reasoning_effort")
    else:
        params["max_tokens"] = config.get("max_tokens")
        params["temperature"] = config.get("temperature")
        params["frequency_penalty"] = config.get("frequency_penalty")
        params["presence_penalty"] = config.get("presence_penalty")
        params["top_p"] = config.get("top_p")

    if config.get("response_format"):
        params["response_format"] = config["response_format"]

    return params
