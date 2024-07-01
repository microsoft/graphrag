# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class LocalSearchConfig(BaseModel):
    """The default configuration section for Cache."""

    text_unit_prop: float = Field(
        description="The text unit proportion.",
        default=defs.LOCAL_SEARCH_TEXT_UNIT_PROP,
    )
    community_prop: float = Field(
        description="The community proportion.",
        default=defs.LOCAL_SEARCH_COMMUNITY_PROP,
    )
    conversation_history_max_turns: int = Field(
        description="The conversation history maximum turns.",
        default=defs.LOCAL_SEARCH_CONVERSATION_HISTORY_MAX_TURNS,
    )
    top_k_entities: int = Field(
        description="The top k mapped entities.",
        default=defs.LOCAL_SEARCH_TOP_K_MAPPED_ENTITIES,
    )
    top_k_relationships: int = Field(
        description="The top k mapped relations.",
        default=defs.LOCAL_SEARCH_TOP_K_RELATIONSHIPS,
    )
    max_tokens: int = Field(
        description="The maximum tokens.", default=defs.LOCAL_SEARCH_MAX_TOKENS
    )
    llm_max_tokens: int = Field(
        description="The LLM maximum tokens.", default=defs.LOCAL_SEARCH_LLM_MAX_TOKENS
    )
