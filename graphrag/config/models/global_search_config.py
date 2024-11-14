# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class GlobalSearchConfig(BaseModel):
    """The default configuration section for Cache."""

    map_prompt: str | None = Field(
        description="The global search mapper prompt to use.", default=None
    )
    reduce_prompt: str | None = Field(
        description="The global search reducer to use.", default=None
    )
    knowledge_prompt: str | None = Field(
        description="The global search general prompt to use.", default=None
    )
    temperature: float | None = Field(
        description="The temperature to use for token generation.",
        default=defs.GLOBAL_SEARCH_LLM_TEMPERATURE,
    )
    top_p: float | None = Field(
        description="The top-p value to use for token generation.",
        default=defs.GLOBAL_SEARCH_LLM_TOP_P,
    )
    n: int | None = Field(
        description="The number of completions to generate.",
        default=defs.GLOBAL_SEARCH_LLM_N,
    )
    max_tokens: int = Field(
        description="The maximum context size in tokens.",
        default=defs.GLOBAL_SEARCH_MAX_TOKENS,
    )
    data_max_tokens: int = Field(
        description="The data llm maximum tokens.",
        default=defs.GLOBAL_SEARCH_DATA_MAX_TOKENS,
    )
    map_max_tokens: int = Field(
        description="The map llm maximum tokens.",
        default=defs.GLOBAL_SEARCH_MAP_MAX_TOKENS,
    )
    reduce_max_tokens: int = Field(
        description="The reduce llm maximum tokens.",
        default=defs.GLOBAL_SEARCH_REDUCE_MAX_TOKENS,
    )
    concurrency: int = Field(
        description="The number of concurrent requests.",
        default=defs.GLOBAL_SEARCH_CONCURRENCY,
    )

    # configurations for dynamic community selection
    dynamic_search_llm: str = Field(
        description="LLM model to use for dynamic community selection",
        default=defs.DYNAMIC_SEARCH_LLM_MODEL,
    )
    dynamic_search_threshold: int = Field(
        description="Rating threshold in include a community report",
        default=defs.DYNAMIC_SEARCH_RATE_THRESHOLD,
    )
    dynamic_search_keep_parent: bool = Field(
        description="Keep parent community if any of the child communities are relevant",
        default=defs.DYNAMIC_SEARCH_KEEP_PARENT,
    )
    dynamic_search_num_repeats: int = Field(
        description="Number of times to rate the same community report",
        default=defs.DYNAMIC_SEARCH_NUM_REPEATS,
    )
    dynamic_search_use_summary: bool = Field(
        description="Use community summary instead of full_context",
        default=defs.DYNAMIC_SEARCH_USE_SUMMARY,
    )
    dynamic_search_concurrent_coroutines: int = Field(
        description="Number of concurrent coroutines to rate community reports",
        default=defs.DYNAMIC_SEARCH_CONCURRENT_COROUTINES,
    )
    dynamic_search_max_level: int = Field(
        description="The maximum level of community hierarchy to consider if none of the processed communities are relevant",
        default=defs.DYNAMIC_SEARCH_MAX_LEVEL,
    )
