# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults


class BasicSearchConfig(BaseModel):
    """The default configuration section for Cache."""

    prompt: str | None = Field(
        description="The basic search prompt to use.",
        default=graphrag_config_defaults.basic_search.prompt,
    )
    chat_model_id: str = Field(
        description="The model ID to use for basic search.",
        default=graphrag_config_defaults.basic_search.chat_model_id,
    )
    embedding_model_id: str = Field(
        description="The model ID to use for text embeddings.",
        default=graphrag_config_defaults.basic_search.embedding_model_id,
    )
    text_unit_prop: float = Field(
        description="The text unit proportion.",
        default=graphrag_config_defaults.basic_search.text_unit_prop,
    )
    conversation_history_max_turns: int = Field(
        description="The conversation history maximum turns.",
        default=graphrag_config_defaults.basic_search.conversation_history_max_turns,
    )
    temperature: float = Field(
        description="The temperature to use for token generation.",
        default=graphrag_config_defaults.basic_search.temperature,
    )
    top_p: float = Field(
        description="The top-p value to use for token generation.",
        default=graphrag_config_defaults.basic_search.top_p,
    )
    n: int = Field(
        description="The number of completions to generate.",
        default=graphrag_config_defaults.basic_search.n,
    )
    max_tokens: int = Field(
        description="The maximum tokens.",
        default=graphrag_config_defaults.basic_search.max_tokens,
    )
    llm_max_tokens: int = Field(
        description="The LLM maximum tokens.",
        default=graphrag_config_defaults.basic_search.llm_max_tokens,
    )
