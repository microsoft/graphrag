# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults


class LocalSearchConfig(BaseModel):
    """The default configuration section for Cache."""

    prompt: str | None = Field(
        description="The local search prompt to use.",
        default=graphrag_config_defaults.local_search.prompt,
    )
    chat_model_id: str = Field(
        description="The model ID to use for local search.",
        default=graphrag_config_defaults.local_search.chat_model_id,
    )
    embedding_model_id: str = Field(
        description="The model ID to use for text embeddings.",
        default=graphrag_config_defaults.local_search.embedding_model_id,
    )
    text_unit_prop: float = Field(
        description="The text unit proportion.",
        default=graphrag_config_defaults.local_search.text_unit_prop,
    )
    community_prop: float = Field(
        description="The community proportion.",
        default=graphrag_config_defaults.local_search.community_prop,
    )
    conversation_history_max_turns: int = Field(
        description="The conversation history maximum turns.",
        default=graphrag_config_defaults.local_search.conversation_history_max_turns,
    )
    top_k_entities: int = Field(
        description="The top k mapped entities.",
        default=graphrag_config_defaults.local_search.top_k_entities,
    )
    top_k_relationships: int = Field(
        description="The top k mapped relations.",
        default=graphrag_config_defaults.local_search.top_k_relationships,
    )
    max_context_tokens: int = Field(
        description="The maximum tokens.",
        default=graphrag_config_defaults.local_search.max_context_tokens,
    )
