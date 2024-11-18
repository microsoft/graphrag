# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class DRIFTSearchConfig(BaseModel):
    """The default configuration section for Cache."""

    prompt: str | None = Field(
        description="The drift search prompt to use.", default=None
    )
    temperature: float = Field(
        description="The temperature to use for token generation.",
        default=defs.DRIFT_SEARCH_LLM_TEMPERATURE,
    )
    top_p: float = Field(
        description="The top-p value to use for token generation.",
        default=defs.DRIFT_SEARCH_LLM_TOP_P,
    )
    n: int = Field(
        description="The number of completions to generate.",
        default=defs.DRIFT_SEARCH_LLM_N,
    )
    max_tokens: int = Field(
        description="The maximum context size in tokens.",
        default=defs.DRIFT_SEARCH_MAX_TOKENS,
    )
    data_max_tokens: int = Field(
        description="The data llm maximum tokens.",
        default=defs.DRIFT_SEARCH_DATA_MAX_TOKENS,
    )

    concurrency: int = Field(
        description="The number of concurrent requests.",
        default=defs.DRIFT_SEARCH_CONCURRENCY,
    )

    drift_k_followups: int = Field(
        description="The number of top global results to retrieve.",
        default=defs.DRIFT_SEARCH_K_FOLLOW_UPS,
    )

    primer_folds: int = Field(
        description="The number of folds for search priming.",
        default=defs.DRIFT_SEARCH_PRIMER_FOLDS,
    )

    primer_llm_max_tokens: int = Field(
        description="The maximum number of tokens for the LLM in primer.",
        default=defs.DRIFT_SEARCH_PRIMER_MAX_TOKENS,
    )

    n_depth: int = Field(
        description="The number of drift search steps to take.",
        default=defs.DRIFT_N_DEPTH,
    )

    local_search_text_unit_prop: float = Field(
        description="The proportion of search dedicated to text units.",
        default=defs.DRIFT_LOCAL_SEARCH_TEXT_UNIT_PROP,
    )

    local_search_community_prop: float = Field(
        description="The proportion of search dedicated to community properties.",
        default=defs.DRIFT_LOCAL_SEARCH_COMMUNITY_PROP,
    )

    local_search_top_k_mapped_entities: int = Field(
        description="The number of top K entities to map during local search.",
        default=defs.DRIFT_LOCAL_SEARCH_TOP_K_MAPPED_ENTITIES,
    )

    local_search_top_k_relationships: int = Field(
        description="The number of top K relationships to map during local search.",
        default=defs.DRIFT_LOCAL_SEARCH_TOP_K_RELATIONSHIPS,
    )

    local_search_max_data_tokens: int = Field(
        description="The maximum context size in tokens for local search.",
        default=defs.DRIFT_LOCAL_SEARCH_MAX_TOKENS,
    )

    local_search_temperature: float = Field(
        description="The temperature to use for token generation in local search.",
        default=defs.DRIFT_LOCAL_SEARCH_LLM_TEMPERATURE,
    )

    local_search_top_p: float = Field(
        description="The top-p value to use for token generation in local search.",
        default=defs.DRIFT_LOCAL_SEARCH_LLM_TOP_P,
    )

    local_search_n: int = Field(
        description="The number of completions to generate in local search.",
        default=defs.DRIFT_LOCAL_SEARCH_LLM_N,
    )

    local_search_llm_max_gen_tokens: int = Field(
        description="The maximum number of generated tokens for the LLM in local search.",
        default=defs.DRIFT_LOCAL_SEARCH_LLM_MAX_TOKENS,
    )
