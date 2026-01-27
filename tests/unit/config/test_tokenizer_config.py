# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Test tokenizer configuration loading."""

import pytest
from graphrag_llm.config import TokenizerConfig, TokenizerType


def test_litellm_tokenizer_validation() -> None:
    """Test that missing required parameters raise validation errors."""

    with pytest.raises(
        ValueError,
        match="model_id must be specified for LiteLLM tokenizer\\.",
    ):
        _ = TokenizerConfig(
            type=TokenizerType.LiteLLM,
            model_id="",
        )

    with pytest.raises(
        ValueError,
        match="encoding_name must be specified for TikToken tokenizer\\.",
    ):
        _ = TokenizerConfig(
            type=TokenizerType.Tiktoken,
            encoding_name="",
        )

    # passes validation
    _ = TokenizerConfig(
        type=TokenizerType.LiteLLM,
        model_id="openai/gpt-4o",
    )
    _ = TokenizerConfig(
        type=TokenizerType.Tiktoken,
        encoding_name="o200k-base",
    )
