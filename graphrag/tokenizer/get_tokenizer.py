# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Get Tokenizer."""

from graphrag.config.defaults import ENCODING_MODEL
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.tokenizer.litellm_tokenizer import LitellmTokenizer
from graphrag.tokenizer.tiktoken_tokenizer import TiktokenTokenizer
from graphrag.tokenizer.tokenizer import Tokenizer


def get_tokenizer(
    model_config: LanguageModelConfig | None = None,
    encoding_model: str = ENCODING_MODEL,
) -> Tokenizer:
    """
    Get the tokenizer for the given model configuration or fallback to a tiktoken based tokenizer.

    Args
    ----
        model_config: LanguageModelConfig, optional
            The model configuration. If not provided or model_config.encoding_model is manually set,
            use a tiktoken based tokenizer. Otherwise, use a LitellmTokenizer based on the model name.
            LiteLLM supports token encoding/decoding for the range of models it supports.
        encoding_model: str, optional
            A tiktoken encoding model to use if no model configuration is provided. Only used if a
            model configuration is not provided.

    Returns
    -------
        An instance of a Tokenizer.
    """
    if model_config is not None:
        if model_config.encoding_model.strip() != "":
            # User has manually specified a tiktoken encoding model to use for the provided model configuration.
            return TiktokenTokenizer(encoding_name=model_config.encoding_model)

        return LitellmTokenizer(model_name=model_config.model)

    return TiktokenTokenizer(encoding_name=encoding_model)
