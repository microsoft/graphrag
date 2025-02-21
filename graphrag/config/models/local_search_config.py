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
    temperature: float = Field(
        description="The temperature to use for token generation.",
        default=graphrag_config_defaults.local_search.temperature,
    )
    top_p: float = Field(
        description="The top-p value to use for token generation.",
        default=graphrag_config_defaults.local_search.top_p,
    )
    n: int = Field(
        description="The number of completions to generate.",
        default=graphrag_config_defaults.local_search.n,
    )
    max_tokens: int = Field(
        description="The maximum tokens.",
        default=graphrag_config_defaults.local_search.max_tokens,
    )
    llm_max_tokens: int = Field(
        description="The LLM maximum tokens.",
        default=graphrag_config_defaults.local_search.llm_max_tokens,
    )
