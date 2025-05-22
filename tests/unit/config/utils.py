# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from dataclasses import asdict

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
from graphrag.config.models.extract_graph_nlp_config import (
    ExtractGraphNLPConfig,
    TextAnalyzerConfig,
)
from graphrag.config.models.global_search_config import GlobalSearchConfig
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.input_config import InputConfig
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.config.models.local_search_config import LocalSearchConfig
from graphrag.config.models.output_config import OutputConfig
from graphrag.config.models.prune_graph_config import PruneGraphConfig
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
    "type": defs.DEFAULT_CHAT_MODEL_TYPE.value,
    "model": defs.DEFAULT_CHAT_MODEL,
}

DEFAULT_EMBEDDING_MODEL_CONFIG = {
    "api_key": FAKE_API_KEY,
    "type": defs.DEFAULT_EMBEDDING_MODEL_TYPE.value,
    "model": defs.DEFAULT_EMBEDDING_MODEL,
}

DEFAULT_MODEL_CONFIG = {
    defs.DEFAULT_CHAT_MODEL_ID: DEFAULT_CHAT_MODEL_CONFIG,
    defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
}


def get_default_graphrag_config(root_dir: str | None = None) -> GraphRagConfig:
    return GraphRagConfig(**{
        **asdict(defs.graphrag_config_defaults),
        "models": DEFAULT_MODEL_CONFIG,
        **({"root_dir": root_dir} if root_dir else {}),
    })


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
    assert actual.max_completion_tokens == expected.max_completion_tokens
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
    assert actual.retry_strategy == expected.retry_strategy
    assert actual.max_retries == expected.max_retries
    assert actual.max_retry_wait == expected.max_retry_wait
    assert actual.concurrent_requests == expected.concurrent_requests
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
    assert actual.names == expected.names
    assert actual.strategy == expected.strategy
    assert actual.model_id == expected.model_id
    assert actual.vector_store_id == expected.vector_store_id


def assert_chunking_configs(actual: ChunkingConfig, expected: ChunkingConfig) -> None:
    assert actual.size == expected.size
    assert actual.overlap == expected.overlap
    assert actual.group_by_columns == expected.group_by_columns
    assert actual.strategy == expected.strategy
    assert actual.encoding_model == expected.encoding_model
    assert actual.prepend_metadata == expected.prepend_metadata
    assert actual.chunk_size_includes_metadata == expected.chunk_size_includes_metadata


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
    assert actual.model_id == expected.model_id


def assert_text_analyzer_configs(
    actual: TextAnalyzerConfig, expected: TextAnalyzerConfig
) -> None:
    assert actual.extractor_type == expected.extractor_type
    assert actual.model_name == expected.model_name
    assert actual.max_word_length == expected.max_word_length
    assert actual.word_delimiter == expected.word_delimiter
    assert actual.include_named_entities == expected.include_named_entities
    assert actual.exclude_nouns == expected.exclude_nouns
    assert actual.exclude_entity_tags == expected.exclude_entity_tags
    assert actual.exclude_pos_tags == expected.exclude_pos_tags
    assert actual.noun_phrase_tags == expected.noun_phrase_tags
    assert actual.noun_phrase_grammars == expected.noun_phrase_grammars


def assert_extract_graph_nlp_configs(
    actual: ExtractGraphNLPConfig, expected: ExtractGraphNLPConfig
) -> None:
    assert actual.normalize_edge_weights == expected.normalize_edge_weights
    assert_text_analyzer_configs(actual.text_analyzer, expected.text_analyzer)
    assert actual.concurrent_requests == expected.concurrent_requests


def assert_prune_graph_configs(
    actual: PruneGraphConfig, expected: PruneGraphConfig
) -> None:
    assert actual.min_node_freq == expected.min_node_freq
    assert actual.max_node_freq_std == expected.max_node_freq_std
    assert actual.min_node_degree == expected.min_node_degree
    assert actual.max_node_degree_std == expected.max_node_degree_std
    assert actual.min_edge_weight_pct == expected.min_edge_weight_pct
    assert actual.remove_ego_nodes == expected.remove_ego_nodes
    assert actual.lcc_only == expected.lcc_only


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
    assert actual.graph_prompt == expected.graph_prompt
    assert actual.text_prompt == expected.text_prompt
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
    assert actual.max_context_tokens == expected.max_context_tokens


def assert_global_search_configs(
    actual: GlobalSearchConfig, expected: GlobalSearchConfig
) -> None:
    assert actual.map_prompt == expected.map_prompt
    assert actual.reduce_prompt == expected.reduce_prompt
    assert actual.knowledge_prompt == expected.knowledge_prompt
    assert actual.max_context_tokens == expected.max_context_tokens
    assert actual.data_max_tokens == expected.data_max_tokens
    assert actual.map_max_length == expected.map_max_length
    assert actual.reduce_max_length == expected.reduce_max_length
    assert actual.dynamic_search_threshold == expected.dynamic_search_threshold
    assert actual.dynamic_search_keep_parent == expected.dynamic_search_keep_parent
    assert actual.dynamic_search_num_repeats == expected.dynamic_search_num_repeats
    assert actual.dynamic_search_use_summary == expected.dynamic_search_use_summary
    assert actual.dynamic_search_max_level == expected.dynamic_search_max_level


def assert_drift_search_configs(
    actual: DRIFTSearchConfig, expected: DRIFTSearchConfig
) -> None:
    assert actual.prompt == expected.prompt
    assert actual.reduce_prompt == expected.reduce_prompt
    assert actual.data_max_tokens == expected.data_max_tokens
    assert actual.reduce_max_tokens == expected.reduce_max_tokens
    assert actual.reduce_temperature == expected.reduce_temperature
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
    assert actual.k == expected.k


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

    if expected.outputs is not None:
        assert actual.outputs is not None
        assert len(actual.outputs) == len(expected.outputs)
        for a, e in zip(actual.outputs.keys(), expected.outputs.keys(), strict=True):
            assert_output_configs(actual.outputs[a], expected.outputs[e])
    else:
        assert actual.outputs is None

    assert_update_output_configs(
        actual.update_index_output, expected.update_index_output
    )

    assert_cache_configs(actual.cache, expected.cache)
    assert_input_configs(actual.input, expected.input)
    assert_embed_graph_configs(actual.embed_graph, expected.embed_graph)
    assert_text_embedding_configs(actual.embed_text, expected.embed_text)
    assert_chunking_configs(actual.chunks, expected.chunks)
    assert_snapshots_configs(actual.snapshots, expected.snapshots)
    assert_extract_graph_configs(actual.extract_graph, expected.extract_graph)
    assert_extract_graph_nlp_configs(
        actual.extract_graph_nlp, expected.extract_graph_nlp
    )
    assert_summarize_descriptions_configs(
        actual.summarize_descriptions, expected.summarize_descriptions
    )
    assert_community_reports_configs(
        actual.community_reports, expected.community_reports
    )
    assert_extract_claims_configs(actual.extract_claims, expected.extract_claims)
    assert_prune_graph_configs(actual.prune_graph, expected.prune_graph)
    assert_cluster_graph_configs(actual.cluster_graph, expected.cluster_graph)
    assert_umap_configs(actual.umap, expected.umap)
    assert_local_search_configs(actual.local_search, expected.local_search)
    assert_global_search_configs(actual.global_search, expected.global_search)
    assert_drift_search_configs(actual.drift_search, expected.drift_search)
    assert_basic_search_configs(actual.basic_search, expected.basic_search)
