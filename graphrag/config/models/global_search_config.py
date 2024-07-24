# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class GlobalSearchConfig(BaseModel):
    """The default configuration section for Cache."""

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
