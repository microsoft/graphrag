# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from pydantic import BaseModel

import graphrag.config.defaults as defs
from graphrag.config.models.basic_search_config import BasicSearchConfig
from graphrag.config.models.cache_config import CacheConfig
from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.config.models.cluster_graph_config import ClusterGraphConfig
from graphrag.config.models.community_reports_config import CommunityReportsConfig
from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.config.models.extract_claims_config import ClaimExtractionConfig
from graphrag.config.models.extract_graph_config import ExtractGraphConfig
from graphrag.config.models.global_search_config import GlobalSearchConfig
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.input_config import InputConfig
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.config.models.local_search_config import LocalSearchConfig
from graphrag.config.models.output_config import OutputConfig
from graphrag.config.models.reporting_config import ReportingConfig
from graphrag.config.models.snapshots_config import SnapshotsConfig
from graphrag.config.models.summarize_descriptions_config import (
    SummarizeDescriptionsConfig,
)
from graphrag.config.models.text_embedding_config import TextEmbeddingConfig
from graphrag.config.models.umap_config import UmapConfig
from graphrag.config.models.vector_store_config import VectorStoreConfig

FAKE_API_KEY = "NOT_AN_API_KEY"

DEFAULT_CHAT_MODEL_CONFIG = {
    "api_key": FAKE_API_KEY,
    "type": defs.LLM_TYPE.value,
    "model": defs.LLM_MODEL,
}

DEFAULT_EMBEDDING_MODEL_CONFIG = {
    "api_key": FAKE_API_KEY,
    "type": defs.EMBEDDING_TYPE.value,
    "model": defs.EMBEDDING_MODEL,
}

DEFAULT_MODEL_CONFIG = {
    defs.DEFAULT_CHAT_MODEL_ID: DEFAULT_CHAT_MODEL_CONFIG,
    defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
}

DEFAULT_GRAPHRAG_CONFIG_SETTINGS = {
    "models": DEFAULT_MODEL_CONFIG,
    "vector_store": {
        defs.VECTOR_STORE_DEFAULT_ID: {
            "type": defs.VECTOR_STORE_TYPE,
            "db_uri": defs.VECTOR_STORE_DB_URI,
            "container_name": defs.VECTOR_STORE_CONTAINER_NAME,
            "overwrite": defs.VECTOR_STORE_OVERWRITE,
            "url": None,
            "api_key": None,
            "audience": None,
            "database_name": None,
        },
    },
    "reporting": {
        "type": defs.REPORTING_TYPE,
        "base_dir": defs.REPORTING_BASE_DIR,
        "connection_string": None,
        "container_name": None,
        "storage_account_blob_url": None,
    },
    "output": {
        "type": defs.OUTPUT_TYPE,
        "base_dir": defs.OUTPUT_BASE_DIR,
        "connection_string": None,
        "container_name": None,
        "storage_account_blob_url": None,
    },
    "update_index_output": None,
    "cache": {
        "type": defs.CACHE_TYPE,
        "base_dir": defs.CACHE_BASE_DIR,
        "connection_string": None,
        "container_name": None,
        "storage_account_blob_url": None,
        "cosmosdb_account_url": None,
    },
    "input": {
        "type": defs.INPUT_TYPE,
        "file_type": defs.INPUT_FILE_TYPE,
        "base_dir": defs.INPUT_BASE_DIR,
        "connection_string": None,
        "storage_account_blob_url": None,
        "container_name": None,
        "encoding": defs.INPUT_FILE_ENCODING,
        "file_pattern": defs.INPUT_TEXT_PATTERN,
        "file_filter": None,
        "text_column": defs.INPUT_TEXT_COLUMN,
        "title_column": None,
        "metadata": None,
    },
    "embed_graph": {
        "enabled": defs.NODE2VEC_ENABLED,
        "dimensions": defs.NODE2VEC_DIMENSIONS,
        "num_walks": defs.NODE2VEC_NUM_WALKS,
        "walk_length": defs.NODE2VEC_WALK_LENGTH,
        "window_size": defs.NODE2VEC_WINDOW_SIZE,
        "iterations": defs.NODE2VEC_ITERATIONS,
        "random_seed": defs.NODE2VEC_RANDOM_SEED,
        "use_lcc": defs.USE_LCC,
    },
    "embed_text": {
        "batch_size": defs.EMBEDDING_BATCH_SIZE,
        "batch_max_tokens": defs.EMBEDDING_BATCH_MAX_TOKENS,
        "target": defs.EMBEDDING_TARGET,
        "strategy": None,
        "model_id": defs.EMBEDDING_MODEL_ID,
    },
    "chunks": {
        "size": defs.CHUNK_SIZE,
        "overlap": defs.CHUNK_OVERLAP,
        "group_by_columns": defs.CHUNK_GROUP_BY_COLUMNS,
        "strategy": defs.CHUNK_STRATEGY,
        "encoding_model": defs.ENCODING_MODEL,
    },
    "snapshots": {
        "embeddings": defs.SNAPSHOTS_EMBEDDINGS,
        "graphml": defs.SNAPSHOTS_GRAPHML,
    },
    "extract_graph": {
        "prompt": None,
        "entity_types": defs.EXTRACT_GRAPH_ENTITY_TYPES,
        "max_gleanings": defs.EXTRACT_GRAPH_MAX_GLEANINGS,
        "strategy": None,
        "encoding_model": None,
        "model_id": defs.EXTRACT_GRAPH_MODEL_ID,
    },
    "summarize_descriptions": {
        "prompt": None,
        "max_length": defs.SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
        "strategy": None,
        "model_id": defs.SUMMARIZE_MODEL_ID,
    },
    "community_report": {
        "prompt": None,
        "max_length": defs.COMMUNITY_REPORT_MAX_LENGTH,
        "max_input_length": defs.COMMUNITY_REPORT_MAX_INPUT_LENGTH,
        "strategy": None,
        "model_id": defs.COMMUNITY_REPORT_MODEL_ID,
    },
    "claim_extaction": {
        "enabled": defs.EXTRACT_CLAIMS_ENABLED,
        "prompt": None,
        "description": defs.DESCRIPTION,
        "max_gleanings": defs.CLAIM_MAX_GLEANINGS,
        "strategy": None,
        "encoding_model": None,
        "model_id": defs.EXTRACT_CLAIMS_MODEL_ID,
    },
    "cluster_graph": {
        "max_cluster_size": defs.MAX_CLUSTER_SIZE,
        "use_lcc": defs.USE_LCC,
        "seed": defs.CLUSTER_GRAPH_SEED,
    },
    "umap": {"enabled": defs.UMAP_ENABLED},
    "local_search": {
        "prompt": None,
        "text_unit_prop": defs.LOCAL_SEARCH_TEXT_UNIT_PROP,
        "community_prop": defs.LOCAL_SEARCH_COMMUNITY_PROP,
        "conversation_history_max_turns": defs.LOCAL_SEARCH_CONVERSATION_HISTORY_MAX_TURNS,
        "top_k_entities": defs.LOCAL_SEARCH_TOP_K_MAPPED_ENTITIES,
        "top_k_relationships": defs.LOCAL_SEARCH_TOP_K_RELATIONSHIPS,
        "temperature": defs.LOCAL_SEARCH_LLM_TEMPERATURE,
        "top_p": defs.LOCAL_SEARCH_LLM_TOP_P,
        "n": defs.LOCAL_SEARCH_LLM_N,
        "max_tokens": defs.LOCAL_SEARCH_MAX_TOKENS,
        "llm_max_tokens": defs.LOCAL_SEARCH_LLM_MAX_TOKENS,
    },
    "global_search": {
        "map_prompt": None,
        "reduce_prompt": None,
        "knowledge_prompt": None,
        "temperature": defs.GLOBAL_SEARCH_LLM_TEMPERATURE,
        "top_p": defs.GLOBAL_SEARCH_LLM_TOP_P,
        "n": defs.GLOBAL_SEARCH_LLM_N,
        "max_tokens": defs.GLOBAL_SEARCH_MAX_TOKENS,
        "data_max_tokens": defs.GLOBAL_SEARCH_DATA_MAX_TOKENS,
        "map_max_tokens": defs.GLOBAL_SEARCH_MAP_MAX_TOKENS,
        "reduce_max_tokens": defs.GLOBAL_SEARCH_REDUCE_MAX_TOKENS,
        "concurrency": defs.GLOBAL_SEARCH_CONCURRENCY,
        "dynamic_search_llm": defs.DYNAMIC_SEARCH_LLM_MODEL,
        "dynamic_search_threshold": defs.DYNAMIC_SEARCH_RATE_THRESHOLD,
        "dynamic_search_keep_parent": defs.DYNAMIC_SEARCH_KEEP_PARENT,
        "dynamic_search_num_repeats": defs.DYNAMIC_SEARCH_NUM_REPEATS,
        "dynamic_search_use_summary": defs.DYNAMIC_SEARCH_USE_SUMMARY,
        "dynamic_search_concurrent_coroutines": defs.DYNAMIC_SEARCH_CONCURRENT_COROUTINES,
        "dynamic_search_max_level": defs.DYNAMIC_SEARCH_MAX_LEVEL,
    },
    "drift_search": {
        "prompt": None,
        "temperature": defs.DRIFT_SEARCH_LLM_TEMPERATURE,
        "top_p": defs.DRIFT_SEARCH_LLM_TOP_P,
        "n": defs.DRIFT_SEARCH_LLM_N,
        "max_tokens": defs.DRIFT_SEARCH_MAX_TOKENS,
        "data_max_tokens": defs.DRIFT_SEARCH_DATA_MAX_TOKENS,
        "concurrency": defs.DRIFT_SEARCH_CONCURRENCY,
        "drift_k_followups": defs.DRIFT_SEARCH_K_FOLLOW_UPS,
        "primer_folds": defs.DRIFT_SEARCH_PRIMER_FOLDS,
        "primer_llm_max_tokens": defs.DRIFT_SEARCH_PRIMER_MAX_TOKENS,
        "n_depth": defs.DRIFT_N_DEPTH,
        "local_search_text_unit_prop": defs.DRIFT_LOCAL_SEARCH_TEXT_UNIT_PROP,
        "local_search_community_prop": defs.DRIFT_LOCAL_SEARCH_COMMUNITY_PROP,
        "local_search_top_k_mapped_entities": defs.DRIFT_LOCAL_SEARCH_TOP_K_MAPPED_ENTITIES,
        "local_search_top_k_relationships": defs.DRIFT_LOCAL_SEARCH_TOP_K_RELATIONSHIPS,
        "local_search_max_data_tokens": defs.DRIFT_LOCAL_SEARCH_MAX_TOKENS,
        "local_search_temperature": defs.DRIFT_LOCAL_SEARCH_LLM_TEMPERATURE,
        "local_search_top_p": defs.DRIFT_LOCAL_SEARCH_LLM_TOP_P,
        "local_search_n": defs.DRIFT_LOCAL_SEARCH_LLM_N,
        "local_search_max_tokens": defs.DRIFT_LOCAL_SEARCH_MAX_TOKENS,
    },
    "basic_search": {
        "prompt": None,
        "text_unit_prop": defs.BASIC_SEARCH_TEXT_UNIT_PROP,
        "conversation_history_max_turns": defs.BASIC_SEARCH_CONVERSATION_HISTORY_MAX_TURNS,
        "temperature": defs.BASIC_SEARCH_LLM_TEMPERATURE,
        "top_p": defs.BASIC_SEARCH_LLM_TOP_P,
        "n": defs.BASIC_SEARCH_LLM_N,
        "max_tokens": defs.BASIC_SEARCH_MAX_TOKENS,
        "llm_max_tokens": defs.BASIC_SEARCH_LLM_MAX_TOKENS,
    },
}


def get_default_graphrag_config(root_dir: str | None = None) -> GraphRagConfig:
    if root_dir is not None and root_dir.strip() != "":
        DEFAULT_GRAPHRAG_CONFIG_SETTINGS["root_dir"] = root_dir

    return GraphRagConfig(**DEFAULT_GRAPHRAG_CONFIG_SETTINGS)


def assert_language_model_configs(
    actual: LanguageModelConfig, expected: LanguageModelConfig
) -> None:
    assert actual.api_key == expected.api_key
    assert actual.auth_type == expected.auth_type
    assert actual.type == expected.type
    assert actual.model == expected.model
    assert actual.encoding_model == expected.encoding_model
    assert actual.max_tokens == expected.max_tokens
    assert actual.temperature == expected.temperature
    assert actual.top_p == expected.top_p
    assert actual.n == expected.n
    assert actual.frequency_penalty == expected.frequency_penalty
    assert actual.presence_penalty == expected.presence_penalty
    assert actual.request_timeout == expected.request_timeout
    assert actual.api_base == expected.api_base
    assert actual.api_version == expected.api_version
    assert actual.deployment_name == expected.deployment_name
    assert actual.organization == expected.organization
    assert actual.proxy == expected.proxy
    assert actual.audience == expected.audience
    assert actual.model_supports_json == expected.model_supports_json
    assert actual.tokens_per_minute == expected.tokens_per_minute
    assert actual.requests_per_minute == expected.requests_per_minute
    assert actual.max_retries == expected.max_retries
    assert actual.max_retry_wait == expected.max_retry_wait
    assert (
        actual.sleep_on_rate_limit_recommendation
        == expected.sleep_on_rate_limit_recommendation
    )
    assert actual.concurrent_requests == expected.concurrent_requests
    assert actual.parallelization_stagger == expected.parallelization_stagger
    assert actual.parallelization_num_threads == expected.parallelization_num_threads
    assert actual.async_mode == expected.async_mode
    if actual.responses is not None:
        assert expected.responses is not None
        assert len(actual.responses) == len(expected.responses)
        for e, a in zip(actual.responses, expected.responses, strict=True):
            assert isinstance(e, BaseModel)
            assert isinstance(a, BaseModel)
            assert e.model_dump() == a.model_dump()
    else:
        assert expected.responses is None


def assert_vector_store_configs(
    actual: dict[str, VectorStoreConfig],
    expected: dict[str, VectorStoreConfig],
):
    assert type(actual) is type(expected)
    assert len(actual) == len(expected)
    for (index_a, store_a), (index_e, store_e) in zip(
        actual.items(), expected.items(), strict=True
    ):
        assert index_a == index_e
        assert store_a.type == store_e.type
        assert store_a.db_uri == store_e.db_uri
        assert store_a.url == store_e.url
        assert store_a.api_key == store_e.api_key
        assert store_a.audience == store_e.audience
        assert store_a.container_name == store_e.container_name
        assert store_a.overwrite == store_e.overwrite
        assert store_a.database_name == store_e.database_name


def assert_reporting_configs(
    actual: ReportingConfig, expected: ReportingConfig
) -> None:
    assert actual.type == expected.type
    assert actual.base_dir == expected.base_dir
    assert actual.connection_string == expected.connection_string
    assert actual.container_name == expected.container_name
    assert actual.storage_account_blob_url == expected.storage_account_blob_url


def assert_output_configs(actual: OutputConfig, expected: OutputConfig) -> None:
    assert expected.type == actual.type
    assert expected.base_dir == actual.base_dir
    assert expected.connection_string == actual.connection_string
    assert expected.container_name == actual.container_name
    assert expected.storage_account_blob_url == actual.storage_account_blob_url
    assert expected.cosmosdb_account_url == actual.cosmosdb_account_url


def assert_update_output_configs(actual: OutputConfig, expected: OutputConfig) -> None:
    assert expected.type == actual.type
    assert expected.base_dir == actual.base_dir
    assert expected.connection_string == actual.connection_string
    assert expected.container_name == actual.container_name
    assert expected.storage_account_blob_url == actual.storage_account_blob_url
    assert expected.cosmosdb_account_url == actual.cosmosdb_account_url


def assert_cache_configs(actual: CacheConfig, expected: CacheConfig) -> None:
    assert actual.type == expected.type
    assert actual.base_dir == expected.base_dir
    assert actual.connection_string == expected.connection_string
    assert actual.container_name == expected.container_name
    assert actual.storage_account_blob_url == expected.storage_account_blob_url
    assert actual.cosmosdb_account_url == expected.cosmosdb_account_url


def assert_input_configs(actual: InputConfig, expected: InputConfig) -> None:
    assert actual.type == expected.type
    assert actual.file_type == expected.file_type
    assert actual.base_dir == expected.base_dir
    assert actual.connection_string == expected.connection_string
    assert actual.storage_account_blob_url == expected.storage_account_blob_url
    assert actual.container_name == expected.container_name
    assert actual.encoding == expected.encoding
    assert actual.file_pattern == expected.file_pattern
    assert actual.file_filter == expected.file_filter
    assert actual.text_column == expected.text_column
    assert actual.title_column == expected.title_column
    assert actual.metadata == expected.metadata


def assert_embed_graph_configs(
    actual: EmbedGraphConfig, expected: EmbedGraphConfig
) -> None:
    assert actual.enabled == expected.enabled
    assert actual.dimensions == expected.dimensions
    assert actual.num_walks == expected.num_walks
    assert actual.walk_length == expected.walk_length
    assert actual.window_size == expected.window_size
    assert actual.iterations == expected.iterations
    assert actual.random_seed == expected.random_seed
    assert actual.use_lcc == expected.use_lcc


def assert_text_embedding_configs(
    actual: TextEmbeddingConfig, expected: TextEmbeddingConfig
) -> None:
    assert actual.batch_size == expected.batch_size
    assert actual.batch_max_tokens == expected.batch_max_tokens
    assert actual.target == expected.target
    assert actual.names == expected.names
    assert actual.strategy == expected.strategy
    assert actual.model_id == expected.model_id


def assert_chunking_configs(actual: ChunkingConfig, expected: ChunkingConfig) -> None:
    assert actual.size == expected.size
    assert actual.overlap == expected.overlap
    assert actual.group_by_columns == expected.group_by_columns
    assert actual.strategy == expected.strategy
    assert actual.encoding_model == expected.encoding_model


def assert_snapshots_configs(
    actual: SnapshotsConfig, expected: SnapshotsConfig
) -> None:
    assert actual.embeddings == expected.embeddings
    assert actual.graphml == expected.graphml


def assert_extract_graph_configs(
    actual: ExtractGraphConfig, expected: ExtractGraphConfig
) -> None:
    assert actual.prompt == expected.prompt
    assert actual.entity_types == expected.entity_types
    assert actual.max_gleanings == expected.max_gleanings
    assert actual.strategy == expected.strategy
    assert actual.encoding_model == expected.encoding_model
    assert actual.model_id == expected.model_id


def assert_summarize_descriptions_configs(
    actual: SummarizeDescriptionsConfig, expected: SummarizeDescriptionsConfig
) -> None:
    assert actual.prompt == expected.prompt
    assert actual.max_length == expected.max_length
    assert actual.strategy == expected.strategy
    assert actual.model_id == expected.model_id


def assert_community_reports_configs(
    actual: CommunityReportsConfig, expected: CommunityReportsConfig
) -> None:
    assert actual.prompt == expected.prompt
    assert actual.max_length == expected.max_length
    assert actual.max_input_length == expected.max_input_length
    assert actual.strategy == expected.strategy
    assert actual.model_id == expected.model_id


def assert_extract_claims_configs(
    actual: ClaimExtractionConfig, expected: ClaimExtractionConfig
) -> None:
    assert actual.enabled == expected.enabled
    assert actual.prompt == expected.prompt
    assert actual.description == expected.description
    assert actual.max_gleanings == expected.max_gleanings
    assert actual.strategy == expected.strategy
    assert actual.encoding_model == expected.encoding_model
    assert actual.model_id == expected.model_id


def assert_cluster_graph_configs(
    actual: ClusterGraphConfig, expected: ClusterGraphConfig
) -> None:
    assert actual.max_cluster_size == expected.max_cluster_size
    assert actual.use_lcc == expected.use_lcc
    assert actual.seed == expected.seed


def assert_umap_configs(actual: UmapConfig, expected: UmapConfig) -> None:
    assert actual.enabled == expected.enabled


def assert_local_search_configs(
    actual: LocalSearchConfig, expected: LocalSearchConfig
) -> None:
    assert actual.prompt == expected.prompt
    assert actual.text_unit_prop == expected.text_unit_prop
    assert actual.community_prop == expected.community_prop
    assert (
        actual.conversation_history_max_turns == expected.conversation_history_max_turns
    )
    assert actual.top_k_entities == expected.top_k_entities
    assert actual.top_k_relationships == expected.top_k_relationships
    assert actual.temperature == expected.temperature
    assert actual.top_p == expected.top_p
    assert actual.n == expected.n
    assert actual.max_tokens == expected.max_tokens
    assert actual.llm_max_tokens == expected.llm_max_tokens


def assert_global_search_configs(
    actual: GlobalSearchConfig, expected: GlobalSearchConfig
) -> None:
    assert actual.map_prompt == expected.map_prompt
    assert actual.reduce_prompt == expected.reduce_prompt
    assert actual.knowledge_prompt == expected.knowledge_prompt
    assert actual.temperature == expected.temperature
    assert actual.top_p == expected.top_p
    assert actual.n == expected.n
    assert actual.max_tokens == expected.max_tokens
    assert actual.data_max_tokens == expected.data_max_tokens
    assert actual.map_max_tokens == expected.map_max_tokens
    assert actual.reduce_max_tokens == expected.reduce_max_tokens
    assert actual.concurrency == expected.concurrency
    assert actual.dynamic_search_llm == expected.dynamic_search_llm
    assert actual.dynamic_search_threshold == expected.dynamic_search_threshold
    assert actual.dynamic_search_keep_parent == expected.dynamic_search_keep_parent
    assert actual.dynamic_search_num_repeats == expected.dynamic_search_num_repeats
    assert actual.dynamic_search_use_summary == expected.dynamic_search_use_summary
    assert (
        actual.dynamic_search_concurrent_coroutines
        == expected.dynamic_search_concurrent_coroutines
    )
    assert actual.dynamic_search_max_level == expected.dynamic_search_max_level


def assert_drift_search_configs(
    actual: DRIFTSearchConfig, expected: DRIFTSearchConfig
) -> None:
    assert actual.prompt == expected.prompt
    assert actual.temperature == expected.temperature
    assert actual.top_p == expected.top_p
    assert actual.n == expected.n
    assert actual.max_tokens == expected.max_tokens
    assert actual.data_max_tokens == expected.data_max_tokens
    assert actual.concurrency == expected.concurrency
    assert actual.drift_k_followups == expected.drift_k_followups
    assert actual.primer_folds == expected.primer_folds
    assert actual.primer_llm_max_tokens == expected.primer_llm_max_tokens
    assert actual.n_depth == expected.n_depth
    assert actual.local_search_text_unit_prop == expected.local_search_text_unit_prop
    assert actual.local_search_community_prop == expected.local_search_community_prop
    assert (
        actual.local_search_top_k_mapped_entities
        == expected.local_search_top_k_mapped_entities
    )
    assert (
        actual.local_search_top_k_relationships
        == expected.local_search_top_k_relationships
    )
    assert actual.local_search_max_data_tokens == expected.local_search_max_data_tokens
    assert actual.local_search_temperature == expected.local_search_temperature
    assert actual.local_search_top_p == expected.local_search_top_p
    assert actual.local_search_n == expected.local_search_n
    assert (
        actual.local_search_llm_max_gen_tokens
        == expected.local_search_llm_max_gen_tokens
    )


def assert_basic_search_configs(
    actual: BasicSearchConfig, expected: BasicSearchConfig
) -> None:
    assert actual.prompt == expected.prompt
    assert actual.text_unit_prop == expected.text_unit_prop
    assert (
        actual.conversation_history_max_turns == expected.conversation_history_max_turns
    )
    assert actual.temperature == expected.temperature
    assert actual.top_p == expected.top_p
    assert actual.n == expected.n
    assert actual.max_tokens == expected.max_tokens
    assert actual.llm_max_tokens == expected.llm_max_tokens


def assert_graphrag_configs(actual: GraphRagConfig, expected: GraphRagConfig) -> None:
    assert actual.root_dir == expected.root_dir

    a_keys = sorted(actual.models.keys())
    e_keys = sorted(expected.models.keys())
    assert len(a_keys) == len(e_keys)
    for a, e in zip(a_keys, e_keys, strict=False):
        assert a == e
        assert_language_model_configs(actual.models[a], expected.models[e])

    assert_vector_store_configs(actual.vector_store, expected.vector_store)
    assert_reporting_configs(actual.reporting, expected.reporting)
    assert_output_configs(actual.output, expected.output)

    if actual.update_index_output is not None:
        assert expected.update_index_output is not None
        assert_update_output_configs(
            actual.update_index_output, expected.update_index_output
        )
    else:
        assert expected.update_index_output is None

    assert_cache_configs(actual.cache, expected.cache)
    assert_input_configs(actual.input, expected.input)
    assert_embed_graph_configs(actual.embed_graph, expected.embed_graph)
    assert_text_embedding_configs(actual.embed_text, expected.embed_text)
    assert_chunking_configs(actual.chunks, expected.chunks)
    assert_snapshots_configs(actual.snapshots, expected.snapshots)
    assert_extract_graph_configs(actual.extract_graph, expected.extract_graph)
    assert_summarize_descriptions_configs(
        actual.summarize_descriptions, expected.summarize_descriptions
    )
    assert_community_reports_configs(
        actual.community_reports, expected.community_reports
    )
    assert_extract_claims_configs(actual.extract_claims, expected.extract_claims)
    assert_cluster_graph_configs(actual.cluster_graph, expected.cluster_graph)
    assert_umap_configs(actual.umap, expected.umap)
    assert_local_search_configs(actual.local_search, expected.local_search)
    assert_global_search_configs(actual.global_search, expected.global_search)
    assert_drift_search_configs(actual.drift_search, expected.drift_search)
