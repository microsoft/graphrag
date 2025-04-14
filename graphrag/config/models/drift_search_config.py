# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults


class DRIFTSearchConfig(BaseModel):
    """The default configuration section for Cache."""

    prompt: str | None = Field(
        description="The drift search prompt to use.",
        default=graphrag_config_defaults.drift_search.prompt,
    )
    reduce_prompt: str | None = Field(
        description="The drift search reduce prompt to use.",
        default=graphrag_config_defaults.drift_search.reduce_prompt,
    )
    chat_model_id: str = Field(
        description="The model ID to use for drift search.",
        default=graphrag_config_defaults.drift_search.chat_model_id,
    )
    embedding_model_id: str = Field(
        description="The model ID to use for drift search.",
        default=graphrag_config_defaults.drift_search.embedding_model_id,
    )
    data_max_tokens: int = Field(
        description="The data llm maximum tokens.",
        default=graphrag_config_defaults.drift_search.data_max_tokens,
    )

    reduce_max_tokens: int | None = Field(
        description="The reduce llm maximum tokens response to produce.",
        default=graphrag_config_defaults.drift_search.reduce_max_tokens,
    )

    reduce_temperature: float = Field(
        description="The temperature to use for token generation in reduce.",
        default=graphrag_config_defaults.drift_search.reduce_temperature,
    )

    reduce_max_completion_tokens: int | None = Field(
        description="The reduce llm maximum tokens response to produce.",
        default=graphrag_config_defaults.drift_search.reduce_max_completion_tokens,
    )

    concurrency: int = Field(
        description="The number of concurrent requests.",
        default=graphrag_config_defaults.drift_search.concurrency,
    )

    drift_k_followups: int = Field(
        description="The number of top global results to retrieve.",
        default=graphrag_config_defaults.drift_search.drift_k_followups,
    )

    primer_folds: int = Field(
        description="The number of folds for search priming.",
        default=graphrag_config_defaults.drift_search.primer_folds,
    )

    primer_llm_max_tokens: int = Field(
        description="The maximum number of tokens for the LLM in primer.",
        default=graphrag_config_defaults.drift_search.primer_llm_max_tokens,
    )

    n_depth: int = Field(
        description="The number of drift search steps to take.",
        default=graphrag_config_defaults.drift_search.n_depth,
    )

    local_search_text_unit_prop: float = Field(
        description="The proportion of search dedicated to text units.",
        default=graphrag_config_defaults.drift_search.local_search_text_unit_prop,
    )

    local_search_community_prop: float = Field(
        description="The proportion of search dedicated to community properties.",
        default=graphrag_config_defaults.drift_search.local_search_community_prop,
    )

    local_search_top_k_mapped_entities: int = Field(
        description="The number of top K entities to map during local search.",
        default=graphrag_config_defaults.drift_search.local_search_top_k_mapped_entities,
    )

    local_search_top_k_relationships: int = Field(
        description="The number of top K relationships to map during local search.",
        default=graphrag_config_defaults.drift_search.local_search_top_k_relationships,
    )

    local_search_max_data_tokens: int = Field(
        description="The maximum context size in tokens for local search.",
        default=graphrag_config_defaults.drift_search.local_search_max_data_tokens,
    )

    local_search_temperature: float = Field(
        description="The temperature to use for token generation in local search.",
        default=graphrag_config_defaults.drift_search.local_search_temperature,
    )

    local_search_top_p: float = Field(
        description="The top-p value to use for token generation in local search.",
        default=graphrag_config_defaults.drift_search.local_search_top_p,
    )

    local_search_n: int = Field(
        description="The number of completions to generate in local search.",
        default=graphrag_config_defaults.drift_search.local_search_n,
    )

    local_search_llm_max_gen_tokens: int | None = Field(
        description="The maximum number of generated tokens for the LLM in local search.",
        default=graphrag_config_defaults.drift_search.local_search_llm_max_gen_tokens,
    )

    local_search_llm_max_gen_completion_tokens: int | None = Field(
        description="The maximum number of generated tokens for the LLM in local search.",
        default=graphrag_config_defaults.drift_search.local_search_llm_max_gen_completion_tokens,
    )
