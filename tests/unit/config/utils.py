# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from dataclasses import asdict

import graphrag.config.defaults as defs
from graphrag.config.models.basic_search_config import BasicSearchConfig
from graphrag.config.models.cluster_graph_config import ClusterGraphConfig
from graphrag.config.models.community_reports_config import CommunityReportsConfig
from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.config.models.embed_text_config import EmbedTextConfig
from graphrag.config.models.extract_claims_config import ExtractClaimsConfig
from graphrag.config.models.extract_graph_config import ExtractGraphConfig
from graphrag.config.models.extract_graph_nlp_config import (
    ExtractGraphNLPConfig,
    TextAnalyzerConfig,
)
from graphrag.config.models.global_search_config import GlobalSearchConfig
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.local_search_config import LocalSearchConfig
from graphrag.config.models.prune_graph_config import PruneGraphConfig
from graphrag.config.models.reporting_config import ReportingConfig
from graphrag.config.models.snapshots_config import SnapshotsConfig
from graphrag.config.models.summarize_descriptions_config import (
    SummarizeDescriptionsConfig,
)
from graphrag_cache import CacheConfig
from graphrag_chunking.chunking_config import ChunkingConfig
from graphrag_input import InputConfig
from graphrag_llm.config import MetricsConfig, ModelConfig, RateLimitConfig, RetryConfig
from graphrag_storage import StorageConfig
from graphrag_vectors import VectorStoreConfig

FAKE_API_KEY = "NOT_AN_API_KEY"

DEFAULT_COMPLETION_MODEL_CONFIG = {
    "api_key": FAKE_API_KEY,
    "model": defs.DEFAULT_COMPLETION_MODEL,
    "model_provider": defs.DEFAULT_MODEL_PROVIDER,
}

DEFAULT_EMBEDDING_MODEL_CONFIG = {
    "api_key": FAKE_API_KEY,
    "model": defs.DEFAULT_EMBEDDING_MODEL,
    "model_provider": defs.DEFAULT_MODEL_PROVIDER,
}

DEFAULT_COMPLETION_MODELS = {
    defs.DEFAULT_COMPLETION_MODEL_ID: DEFAULT_COMPLETION_MODEL_CONFIG,
}

DEFAULT_EMBEDDING_MODELS = {
    defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
}


def get_default_graphrag_config() -> GraphRagConfig:
    return GraphRagConfig(**{
        **asdict(defs.graphrag_config_defaults),
        "completion_models": DEFAULT_COMPLETION_MODELS,
        "embedding_models": DEFAULT_EMBEDDING_MODELS,
    })


def assert_retry_configs(actual: RetryConfig, expected: RetryConfig) -> None:
    assert actual.type == expected.type
    assert actual.max_retries == expected.max_retries
    assert actual.base_delay == expected.base_delay
    assert actual.jitter == expected.jitter
    assert actual.max_delay == expected.max_delay


def assert_rate_limit_configs(
    actual: RateLimitConfig, expected: RateLimitConfig
) -> None:
    assert actual.type == expected.type
    assert actual.period_in_seconds == expected.period_in_seconds
    assert actual.requests_per_period == expected.requests_per_period
    assert actual.tokens_per_period == expected.tokens_per_period


def assert_metrics_configs(actual: MetricsConfig, expected: MetricsConfig) -> None:
    assert actual.type == expected.type
    assert actual.store == expected.store
    assert actual.writer == expected.writer
    assert actual.log_level == expected.log_level
    assert actual.base_dir == expected.base_dir


def assert_model_configs(actual: ModelConfig, expected: ModelConfig) -> None:
    assert actual.type == expected.type
    assert actual.model_provider == expected.model_provider
    assert actual.model == expected.model
    assert actual.call_args == expected.call_args
    assert actual.api_base == expected.api_base
    assert actual.api_version == expected.api_version
    assert actual.api_key == expected.api_key
    assert actual.auth_method == expected.auth_method
    assert actual.azure_deployment_name == expected.azure_deployment_name
    if actual.retry and expected.retry:
        assert_retry_configs(actual.retry, expected.retry)
    else:
        assert actual.retry == expected.retry
    if actual.rate_limit and expected.rate_limit:
        assert_rate_limit_configs(actual.rate_limit, expected.rate_limit)
    else:
        assert actual.rate_limit == expected.rate_limit
    if actual.metrics and expected.metrics:
        assert_metrics_configs(actual.metrics, expected.metrics)
    else:
        assert actual.metrics == expected.metrics
    assert actual.mock_responses == expected.mock_responses


def assert_vector_store_configs(
    actual: VectorStoreConfig,
    expected: VectorStoreConfig,
):
    assert type(actual) is type(expected)
    assert actual.type == expected.type
    assert actual.db_uri == expected.db_uri
    assert actual.url == expected.url
    assert actual.api_key == expected.api_key
    assert actual.audience == expected.audience
    assert actual.database_name == expected.database_name


def assert_reporting_configs(
    actual: ReportingConfig, expected: ReportingConfig
) -> None:
    assert actual.type == expected.type
    assert actual.base_dir == expected.base_dir
    assert actual.connection_string == expected.connection_string
    assert actual.container_name == expected.container_name
    assert actual.account_url == expected.account_url


def assert_storage_config(actual: StorageConfig, expected: StorageConfig) -> None:
    assert expected.type == actual.type
    assert expected.base_dir == actual.base_dir
    assert expected.connection_string == actual.connection_string
    assert expected.container_name == actual.container_name
    assert expected.account_url == actual.account_url
    assert expected.encoding == actual.encoding
    assert expected.database_name == actual.database_name


def assert_cache_configs(actual: CacheConfig, expected: CacheConfig) -> None:
    assert actual.type == expected.type
    if actual.storage and expected.storage:
        assert_storage_config(actual.storage, expected.storage)


def assert_input_configs(actual: InputConfig, expected: InputConfig) -> None:
    assert actual.type == expected.type
    assert actual.encoding == expected.encoding
    assert actual.file_pattern == expected.file_pattern
    assert actual.text_column == expected.text_column
    assert actual.title_column == expected.title_column


def assert_text_embedding_configs(
    actual: EmbedTextConfig, expected: EmbedTextConfig
) -> None:
    assert actual.batch_size == expected.batch_size
    assert actual.batch_max_tokens == expected.batch_max_tokens
    assert actual.names == expected.names
    assert actual.embedding_model_id == expected.embedding_model_id


def assert_chunking_configs(actual: ChunkingConfig, expected: ChunkingConfig) -> None:
    assert actual.size == expected.size
    assert actual.overlap == expected.overlap
    assert actual.type == expected.type
    assert actual.encoding_model == expected.encoding_model
    assert actual.prepend_metadata == expected.prepend_metadata


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
    assert actual.completion_model_id == expected.completion_model_id


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
    assert actual.completion_model_id == expected.completion_model_id


def assert_community_reports_configs(
    actual: CommunityReportsConfig, expected: CommunityReportsConfig
) -> None:
    assert actual.graph_prompt == expected.graph_prompt
    assert actual.text_prompt == expected.text_prompt
    assert actual.max_length == expected.max_length
    assert actual.max_input_length == expected.max_input_length
    assert actual.completion_model_id == expected.completion_model_id


def assert_extract_claims_configs(
    actual: ExtractClaimsConfig, expected: ExtractClaimsConfig
) -> None:
    assert actual.enabled == expected.enabled
    assert actual.prompt == expected.prompt
    assert actual.description == expected.description
    assert actual.max_gleanings == expected.max_gleanings
    assert actual.completion_model_id == expected.completion_model_id


def assert_cluster_graph_configs(
    actual: ClusterGraphConfig, expected: ClusterGraphConfig
) -> None:
    assert actual.max_cluster_size == expected.max_cluster_size
    assert actual.use_lcc == expected.use_lcc
    assert actual.seed == expected.seed


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
    completion_keys = sorted(actual.completion_models.keys())
    expected_completion_keys = sorted(expected.completion_models.keys())
    assert len(completion_keys) == len(expected_completion_keys)
    for a, e in zip(completion_keys, expected_completion_keys, strict=False):
        assert a == e
        assert_model_configs(actual.completion_models[a], expected.completion_models[e])

    embedding_keys = sorted(actual.embedding_models.keys())
    expected_embedding_keys = sorted(expected.embedding_models.keys())
    assert len(embedding_keys) == len(expected_embedding_keys)
    for a, e in zip(embedding_keys, expected_embedding_keys, strict=False):
        assert a == e
        assert_model_configs(actual.embedding_models[a], expected.embedding_models[e])

    assert_vector_store_configs(actual.vector_store, expected.vector_store)
    assert_reporting_configs(actual.reporting, expected.reporting)
    assert_storage_config(actual.output_storage, expected.output_storage)
    assert_storage_config(actual.input_storage, expected.input_storage)
    assert_storage_config(actual.update_output_storage, expected.update_output_storage)

    assert_cache_configs(actual.cache, expected.cache)
    assert_input_configs(actual.input, expected.input)
    assert_text_embedding_configs(actual.embed_text, expected.embed_text)
    assert_chunking_configs(actual.chunking, expected.chunking)
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
    assert_local_search_configs(actual.local_search, expected.local_search)
    assert_global_search_configs(actual.global_search, expected.global_search)
    assert_drift_search_configs(actual.drift_search, expected.drift_search)
    assert_basic_search_configs(actual.basic_search, expected.basic_search)
