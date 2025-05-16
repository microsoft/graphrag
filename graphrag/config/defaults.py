# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Common default configuration values."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from graphrag.config.embeddings import default_embeddings
from graphrag.config.enums import (
    AsyncType,
    AuthType,
    CacheType,
    ChunkStrategyType,
    InputFileType,
    InputType,
    ModelType,
    NounPhraseExtractorType,
    OutputType,
    ReportingType,
)
from graphrag.index.operations.build_noun_graph.np_extractors.stop_words import (
    EN_STOP_WORDS,
)
from graphrag.vector_stores.factory import VectorStoreType

DEFAULT_OUTPUT_BASE_DIR = "output"
DEFAULT_CHAT_MODEL_ID = "default_chat_model"
DEFAULT_CHAT_MODEL_TYPE = ModelType.OpenAIChat
DEFAULT_CHAT_MODEL = "gpt-4-turbo-preview"
DEFAULT_CHAT_MODEL_AUTH_TYPE = AuthType.APIKey
DEFAULT_EMBEDDING_MODEL_ID = "default_embedding_model"
DEFAULT_EMBEDDING_MODEL_TYPE = ModelType.OpenAIEmbedding
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_MODEL_AUTH_TYPE = AuthType.APIKey
DEFAULT_VECTOR_STORE_ID = "default_vector_store"

ENCODING_MODEL = "cl100k_base"
COGNITIVE_SERVICES_AUDIENCE = "https://cognitiveservices.azure.com/.default"


@dataclass
class BasicSearchDefaults:
    """Default values for basic search."""

    prompt: None = None
    k: int = 10
    max_context_tokens: int = 12_000
    chat_model_id: str = DEFAULT_CHAT_MODEL_ID
    embedding_model_id: str = DEFAULT_EMBEDDING_MODEL_ID


@dataclass
class CacheDefaults:
    """Default values for cache."""

    type = CacheType.file
    base_dir: str = "cache"
    connection_string: None = None
    container_name: None = None
    storage_account_blob_url: None = None
    cosmosdb_account_url: None = None


@dataclass
class ChunksDefaults:
    """Default values for chunks."""

    size: int = 1200
    overlap: int = 100
    group_by_columns: list[str] = field(default_factory=lambda: ["id"])
    strategy = ChunkStrategyType.tokens
    encoding_model: str = "cl100k_base"
    prepend_metadata: bool = False
    chunk_size_includes_metadata: bool = False


@dataclass
class ClusterGraphDefaults:
    """Default values for cluster graph."""

    max_cluster_size: int = 10
    use_lcc: bool = True
    seed: int = 0xDEADBEEF


@dataclass
class CommunityReportDefaults:
    """Default values for community report."""

    graph_prompt: None = None
    text_prompt: None = None
    max_length: int = 2000
    max_input_length: int = 8000
    strategy: None = None
    model_id: str = DEFAULT_CHAT_MODEL_ID


@dataclass
class DriftSearchDefaults:
    """Default values for drift search."""

    prompt: None = None
    reduce_prompt: None = None
    data_max_tokens: int = 12_000
    reduce_max_tokens: None = None
    reduce_temperature: float = 0
    reduce_max_completion_tokens: None = None
    concurrency: int = 32
    drift_k_followups: int = 20
    primer_folds: int = 5
    primer_llm_max_tokens: int = 12_000
    n_depth: int = 3
    local_search_text_unit_prop: float = 0.9
    local_search_community_prop: float = 0.1
    local_search_top_k_mapped_entities: int = 10
    local_search_top_k_relationships: int = 10
    local_search_max_data_tokens: int = 12_000
    local_search_temperature: float = 0
    local_search_top_p: float = 1
    local_search_n: int = 1
    local_search_llm_max_gen_tokens = None
    local_search_llm_max_gen_completion_tokens = None
    chat_model_id: str = DEFAULT_CHAT_MODEL_ID
    embedding_model_id: str = DEFAULT_EMBEDDING_MODEL_ID


@dataclass
class EmbedGraphDefaults:
    """Default values for embedding graph."""

    enabled: bool = False
    dimensions: int = 1536
    num_walks: int = 10
    walk_length: int = 40
    window_size: int = 2
    iterations: int = 3
    random_seed: int = 597832
    use_lcc: bool = True


@dataclass
class EmbedTextDefaults:
    """Default values for embedding text."""

    model: str = "text-embedding-3-small"
    batch_size: int = 16
    batch_max_tokens: int = 8191
    model_id: str = DEFAULT_EMBEDDING_MODEL_ID
    names: list[str] = field(default_factory=lambda: default_embeddings)
    strategy: None = None
    vector_store_id: str = DEFAULT_VECTOR_STORE_ID


@dataclass
class ExtractClaimsDefaults:
    """Default values for claim extraction."""

    enabled: bool = False
    prompt: None = None
    description: str = (
        "Any claims or facts that could be relevant to information discovery."
    )
    max_gleanings: int = 1
    strategy: None = None
    model_id: str = DEFAULT_CHAT_MODEL_ID


@dataclass
class ExtractGraphDefaults:
    """Default values for extracting graph."""

    prompt: None = None
    entity_types: list[str] = field(
        default_factory=lambda: ["organization", "person", "geo", "event"]
    )
    max_gleanings: int = 1
    strategy: None = None
    model_id: str = DEFAULT_CHAT_MODEL_ID


@dataclass
class TextAnalyzerDefaults:
    """Default values for text analyzer."""

    extractor_type = NounPhraseExtractorType.RegexEnglish
    model_name: str = "en_core_web_md"
    max_word_length: int = 15
    word_delimiter: str = " "
    include_named_entities: bool = True
    exclude_nouns: list[str] = field(default_factory=lambda: EN_STOP_WORDS)
    exclude_entity_tags: list[str] = field(default_factory=lambda: ["DATE"])
    exclude_pos_tags: list[str] = field(
        default_factory=lambda: ["DET", "PRON", "INTJ", "X"]
    )
    noun_phrase_tags: list[str] = field(default_factory=lambda: ["PROPN", "NOUNS"])
    noun_phrase_grammars: dict[str, str] = field(
        default_factory=lambda: {
            "PROPN,PROPN": "PROPN",
            "NOUN,NOUN": "NOUNS",
            "NOUNS,NOUN": "NOUNS",
            "ADJ,ADJ": "ADJ",
            "ADJ,NOUN": "NOUNS",
        }
    )


@dataclass
class ExtractGraphNLPDefaults:
    """Default values for NLP graph extraction."""

    normalize_edge_weights: bool = True
    text_analyzer: TextAnalyzerDefaults = field(default_factory=TextAnalyzerDefaults)
    concurrent_requests: int = 25


@dataclass
class GlobalSearchDefaults:
    """Default values for global search."""

    map_prompt: None = None
    reduce_prompt: None = None
    knowledge_prompt: None = None
    max_context_tokens: int = 12_000
    data_max_tokens: int = 12_000
    map_max_length: int = 1000
    reduce_max_length: int = 2000
    dynamic_search_threshold: int = 1
    dynamic_search_keep_parent: bool = False
    dynamic_search_num_repeats: int = 1
    dynamic_search_use_summary: bool = False
    dynamic_search_max_level: int = 2
    chat_model_id: str = DEFAULT_CHAT_MODEL_ID


@dataclass
class InputDefaults:
    """Default values for input."""

    type = InputType.file
    file_type = InputFileType.text
    base_dir: str = "input"
    connection_string: None = None
    storage_account_blob_url: None = None
    container_name: None = None
    encoding: str = "utf-8"
    file_pattern: str = ""
    file_filter: None = None
    text_column: str = "text"
    title_column: None = None
    metadata: None = None


@dataclass
class LanguageModelDefaults:
    """Default values for language model."""

    api_key: None = None
    auth_type = AuthType.APIKey
    encoding_model: str = ""
    max_tokens: int | None = None
    temperature: float = 0
    max_completion_tokens: int | None = None
    reasoning_effort: str | None = None
    top_p: float = 1
    n: int = 1
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    request_timeout: float = 180.0
    api_base: None = None
    api_version: None = None
    deployment_name: None = None
    organization: None = None
    proxy: None = None
    audience: None = None
    model_supports_json: None = None
    tokens_per_minute: Literal["auto"] = "auto"
    requests_per_minute: Literal["auto"] = "auto"
    retry_strategy: str = "native"
    max_retries: int = 10
    max_retry_wait: float = 10.0
    concurrent_requests: int = 25
    responses: None = None
    async_mode: AsyncType = AsyncType.Threaded


@dataclass
class LocalSearchDefaults:
    """Default values for local search."""

    prompt: None = None
    text_unit_prop: float = 0.5
    community_prop: float = 0.15
    conversation_history_max_turns: int = 5
    top_k_entities: int = 10
    top_k_relationships: int = 10
    max_context_tokens: int = 12_000
    chat_model_id: str = DEFAULT_CHAT_MODEL_ID
    embedding_model_id: str = DEFAULT_EMBEDDING_MODEL_ID


@dataclass
class OutputDefaults:
    """Default values for output."""

    type = OutputType.file
    base_dir: str = DEFAULT_OUTPUT_BASE_DIR
    connection_string: None = None
    container_name: None = None
    storage_account_blob_url: None = None
    cosmosdb_account_url: None = None


@dataclass
class PruneGraphDefaults:
    """Default values for pruning graph."""

    min_node_freq: int = 2
    max_node_freq_std: None = None
    min_node_degree: int = 1
    max_node_degree_std: None = None
    min_edge_weight_pct: float = 40.0
    remove_ego_nodes: bool = True
    lcc_only: bool = False


@dataclass
class ReportingDefaults:
    """Default values for reporting."""

    type = ReportingType.file
    base_dir: str = "logs"
    connection_string: None = None
    container_name: None = None
    storage_account_blob_url: None = None


@dataclass
class SnapshotsDefaults:
    """Default values for snapshots."""

    embeddings: bool = False
    graphml: bool = False
    raw_graph: bool = False


@dataclass
class SummarizeDescriptionsDefaults:
    """Default values for summarizing descriptions."""

    prompt: None = None
    max_length: int = 500
    max_input_tokens: int = 4_000
    strategy: None = None
    model_id: str = DEFAULT_CHAT_MODEL_ID


@dataclass
class UmapDefaults:
    """Default values for UMAP."""

    enabled: bool = False


@dataclass
class UpdateIndexOutputDefaults:
    """Default values for update index output."""

    type = OutputType.file
    base_dir: str = "update_output"
    connection_string: None = None
    container_name: None = None
    storage_account_blob_url: None = None


@dataclass
class VectorStoreDefaults:
    """Default values for vector stores."""

    type = VectorStoreType.LanceDB.value
    db_uri: str = str(Path(DEFAULT_OUTPUT_BASE_DIR) / "lancedb")
    container_name: str = "default"
    overwrite: bool = True
    url: None = None
    api_key: None = None
    audience: None = None
    database_name: None = None


@dataclass
class GraphRagConfigDefaults:
    """Default values for GraphRAG."""

    root_dir: str = ""
    models: dict = field(default_factory=dict)
    reporting: ReportingDefaults = field(default_factory=ReportingDefaults)
    output: OutputDefaults = field(default_factory=OutputDefaults)
    outputs: None = None
    update_index_output: UpdateIndexOutputDefaults = field(
        default_factory=UpdateIndexOutputDefaults
    )
    cache: CacheDefaults = field(default_factory=CacheDefaults)
    input: InputDefaults = field(default_factory=InputDefaults)
    embed_graph: EmbedGraphDefaults = field(default_factory=EmbedGraphDefaults)
    embed_text: EmbedTextDefaults = field(default_factory=EmbedTextDefaults)
    chunks: ChunksDefaults = field(default_factory=ChunksDefaults)
    snapshots: SnapshotsDefaults = field(default_factory=SnapshotsDefaults)
    extract_graph: ExtractGraphDefaults = field(default_factory=ExtractGraphDefaults)
    extract_graph_nlp: ExtractGraphNLPDefaults = field(
        default_factory=ExtractGraphNLPDefaults
    )
    summarize_descriptions: SummarizeDescriptionsDefaults = field(
        default_factory=SummarizeDescriptionsDefaults
    )
    community_reports: CommunityReportDefaults = field(
        default_factory=CommunityReportDefaults
    )
    extract_claims: ExtractClaimsDefaults = field(default_factory=ExtractClaimsDefaults)
    prune_graph: PruneGraphDefaults = field(default_factory=PruneGraphDefaults)
    cluster_graph: ClusterGraphDefaults = field(default_factory=ClusterGraphDefaults)
    umap: UmapDefaults = field(default_factory=UmapDefaults)
    local_search: LocalSearchDefaults = field(default_factory=LocalSearchDefaults)
    global_search: GlobalSearchDefaults = field(default_factory=GlobalSearchDefaults)
    drift_search: DriftSearchDefaults = field(default_factory=DriftSearchDefaults)
    basic_search: BasicSearchDefaults = field(default_factory=BasicSearchDefaults)
    vector_store: dict[str, VectorStoreDefaults] = field(
        default_factory=lambda: {DEFAULT_VECTOR_STORE_ID: VectorStoreDefaults()}
    )
    workflows: None = None


language_model_defaults = LanguageModelDefaults()
vector_store_defaults = VectorStoreDefaults()
graphrag_config_defaults = GraphRagConfigDefaults()
