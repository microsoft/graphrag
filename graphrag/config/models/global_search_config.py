# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults


class GlobalSearchConfig(BaseModel):
    """The default configuration section for Cache."""

    map_prompt: str | None = Field(
        description="The global search mapper prompt to use.",
        default=graphrag_config_defaults.global_search.map_prompt,
    )
    reduce_prompt: str | None = Field(
        description="The global search reducer to use.",
        default=graphrag_config_defaults.global_search.reduce_prompt,
    )
    chat_model_id: str = Field(
        description="The model ID to use for global search.",
        default=graphrag_config_defaults.global_search.chat_model_id,
    )
    knowledge_prompt: str | None = Field(
        description="The global search general prompt to use.",
        default=graphrag_config_defaults.global_search.knowledge_prompt,
    )
    max_context_tokens: int = Field(
        description="The maximum context size in tokens.",
        default=graphrag_config_defaults.global_search.max_context_tokens,
    )
    data_max_tokens: int = Field(
        description="The data llm maximum tokens.",
        default=graphrag_config_defaults.global_search.data_max_tokens,
    )
    map_max_length: int = Field(
        description="The map llm maximum response length in words.",
        default=graphrag_config_defaults.global_search.map_max_length,
    )
    reduce_max_length: int = Field(
        description="The reduce llm maximum response length in words.",
        default=graphrag_config_defaults.global_search.reduce_max_length,
    )

    # configurations for dynamic community selection
    dynamic_search_threshold: int = Field(
        description="Rating threshold in include a community report",
        default=graphrag_config_defaults.global_search.dynamic_search_threshold,
    )
    dynamic_search_keep_parent: bool = Field(
        description="Keep parent community if any of the child communities are relevant",
        default=graphrag_config_defaults.global_search.dynamic_search_keep_parent,
    )
    dynamic_search_num_repeats: int = Field(
        description="Number of times to rate the same community report",
        default=graphrag_config_defaults.global_search.dynamic_search_num_repeats,
    )
    dynamic_search_use_summary: bool = Field(
        description="Use community summary instead of full_context",
        default=graphrag_config_defaults.global_search.dynamic_search_use_summary,
    )
    dynamic_search_max_level: int = Field(
        description="The maximum level of community hierarchy to consider if none of the processed communities are relevant",
        default=graphrag_config_defaults.global_search.dynamic_search_max_level,
    )
