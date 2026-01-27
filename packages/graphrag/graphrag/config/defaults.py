# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Common default configuration values."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from graphrag_cache import CacheType
from graphrag_chunking.chunk_strategy_type import ChunkerType
from graphrag_input import InputType
from graphrag_llm.config import AuthMethod
from graphrag_storage import StorageType
from graphrag_vectors import VectorStoreType

from graphrag.config.embeddings import default_embeddings
from graphrag.config.enums import (
    AsyncType,
    NounPhraseExtractorType,
    ReportingType,
)
from graphrag.index.operations.build_noun_graph.np_extractors.stop_words import (
    EN_STOP_WORDS,
)

DEFAULT_INPUT_BASE_DIR = "input"
DEFAULT_OUTPUT_BASE_DIR = "output"
DEFAULT_CACHE_BASE_DIR = "cache"
DEFAULT_UPDATE_OUTPUT_BASE_DIR = "update_output"
DEFAULT_COMPLETION_MODEL_ID = "default_completion_model"
DEFAULT_COMPLETION_MODEL_AUTH_TYPE = AuthMethod.ApiKey
DEFAULT_COMPLETION_MODEL = "gpt-4.1"
DEFAULT_EMBEDDING_MODEL_ID = "default_embedding_model"
DEFAULT_EMBEDDING_MODEL_AUTH_TYPE = AuthMethod.ApiKey
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_MODEL_PROVIDER = "openai"

ENCODING_MODEL = "o200k_base"
COGNITIVE_SERVICES_AUDIENCE = "https://cognitiveservices.azure.com/.default"

DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


@dataclass
class BasicSearchDefaults:
    """Default values for basic search."""

    prompt: None = None
    k: int = 10
    max_context_tokens: int = 12_000
    completion_model_id: str = DEFAULT_COMPLETION_MODEL_ID
    embedding_model_id: str = DEFAULT_EMBEDDING_MODEL_ID


@dataclass
class ChunkingDefaults:
    """Default values for chunking."""

    type: str = ChunkerType.Tokens
    size: int = 1200
    overlap: int = 100
    encoding_model: str = ENCODING_MODEL
    prepend_metadata: None = None


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
    completion_model_id: str = DEFAULT_COMPLETION_MODEL_ID
    model_instance_name: str = "community_reporting"


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
    local_search_llm_max_gen_tokens: int | None = None
    local_search_llm_max_gen_completion_tokens: int | None = None
    completion_model_id: str = DEFAULT_COMPLETION_MODEL_ID
    embedding_model_id: str = DEFAULT_EMBEDDING_MODEL_ID


@dataclass
class EmbedTextDefaults:
    """Default values for embedding text."""

    embedding_model_id: str = DEFAULT_EMBEDDING_MODEL_ID
    model_instance_name: str = "text_embedding"
    batch_size: int = 16
    batch_max_tokens: int = 8191
    names: list[str] = field(default_factory=lambda: default_embeddings)


@dataclass
class ExtractClaimsDefaults:
    """Default values for claim extraction."""

    enabled: bool = False
    prompt: None = None
    description: str = (
        "Any claims or facts that could be relevant to information discovery."
    )
    max_gleanings: int = 1
    completion_model_id: str = DEFAULT_COMPLETION_MODEL_ID
    model_instance_name: str = "extract_claims"


@dataclass
class ExtractGraphDefaults:
    """Default values for extracting graph."""

    prompt: None = None
    entity_types: list[str] = field(
        default_factory=lambda: ["organization", "person", "geo", "event"]
    )
    max_gleanings: int = 1
    completion_model_id: str = DEFAULT_COMPLETION_MODEL_ID
    model_instance_name: str = "extract_graph"


@dataclass
class TextAnalyzerDefaults:
    """Default values for text analyzer."""

    extractor_type: ClassVar[NounPhraseExtractorType] = (
        NounPhraseExtractorType.RegexEnglish
    )
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
    async_mode: AsyncType = AsyncType.Threaded


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
    completion_model_id: str = DEFAULT_COMPLETION_MODEL_ID


@dataclass
class StorageDefaults:
    """Default values for storage."""

    type: str = StorageType.File
    encoding: str | None = None
    base_dir: str | None = None
    azure_connection_string: None = None
    azure_container_name: None = None
    azure_account_url: None = None
    azure_cosmosdb_account_url: None = None


@dataclass
class InputDefaults:
    """Default values for input."""

    type: ClassVar[InputType] = InputType.Text
    encoding: str | None = None
    file_pattern: None = None
    id_column: None = None
    title_column: None = None
    text_column: None = None


@dataclass
class InputStorageDefaults(StorageDefaults):
    """Default values for input storage."""

    base_dir: str | None = DEFAULT_INPUT_BASE_DIR


@dataclass
class CacheStorageDefaults(StorageDefaults):
    """Default values for cache storage."""

    base_dir: str | None = DEFAULT_CACHE_BASE_DIR


@dataclass
class CacheDefaults:
    """Default values for cache."""

    type: CacheType = CacheType.Json
    storage: CacheStorageDefaults = field(default_factory=CacheStorageDefaults)


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
    completion_model_id: str = DEFAULT_COMPLETION_MODEL_ID
    embedding_model_id: str = DEFAULT_EMBEDDING_MODEL_ID


@dataclass
class OutputStorageDefaults(StorageDefaults):
    """Default values for output."""

    base_dir: str | None = DEFAULT_OUTPUT_BASE_DIR


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

    type: ClassVar[ReportingType] = ReportingType.file
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
    completion_model_id: str = DEFAULT_COMPLETION_MODEL_ID
    model_instance_name: str = "summarize_descriptions"


@dataclass
class UpdateOutputStorageDefaults(StorageDefaults):
    """Default values for update index output."""

    base_dir: str | None = DEFAULT_UPDATE_OUTPUT_BASE_DIR


@dataclass
class VectorStoreDefaults:
    """Default values for vector stores."""

    type: ClassVar[str] = VectorStoreType.LanceDB.value
    db_uri: str = str(Path(DEFAULT_OUTPUT_BASE_DIR) / "lancedb")


@dataclass
class GraphRagConfigDefaults:
    """Default values for GraphRAG."""

    models: dict = field(default_factory=dict)
    completion_models: dict = field(default_factory=dict)
    embedding_models: dict = field(default_factory=dict)
    concurrent_requests: int = 25
    async_mode: AsyncType = AsyncType.Threaded
    reporting: ReportingDefaults = field(default_factory=ReportingDefaults)
    input_storage: InputStorageDefaults = field(default_factory=InputStorageDefaults)
    output_storage: OutputStorageDefaults = field(default_factory=OutputStorageDefaults)
    update_output_storage: UpdateOutputStorageDefaults = field(
        default_factory=UpdateOutputStorageDefaults
    )
    cache: CacheDefaults = field(default_factory=CacheDefaults)
    input: InputDefaults = field(default_factory=InputDefaults)

    embed_text: EmbedTextDefaults = field(default_factory=EmbedTextDefaults)
    chunking: ChunkingDefaults = field(default_factory=ChunkingDefaults)
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
    local_search: LocalSearchDefaults = field(default_factory=LocalSearchDefaults)
    global_search: GlobalSearchDefaults = field(default_factory=GlobalSearchDefaults)
    drift_search: DriftSearchDefaults = field(default_factory=DriftSearchDefaults)
    basic_search: BasicSearchDefaults = field(default_factory=BasicSearchDefaults)
    vector_store: VectorStoreDefaults = field(
        default_factory=lambda: VectorStoreDefaults()
    )
    workflows: None = None


vector_store_defaults = VectorStoreDefaults()
graphrag_config_defaults = GraphRagConfigDefaults()
