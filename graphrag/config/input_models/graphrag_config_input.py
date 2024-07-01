# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from .cache_config_input import CacheConfigInput
from .chunking_config_input import ChunkingConfigInput
from .claim_extraction_config_input import ClaimExtractionConfigInput
from .cluster_graph_config_input import ClusterGraphConfigInput
from .community_reports_config_input import CommunityReportsConfigInput
from .embed_graph_config_input import EmbedGraphConfigInput
from .entity_extraction_config_input import EntityExtractionConfigInput
from .global_search_config_input import GlobalSearchConfigInput
from .input_config_input import InputConfigInput
from .llm_config_input import LLMConfigInput
from .local_search_config_input import LocalSearchConfigInput
from .reporting_config_input import ReportingConfigInput
from .snapshots_config_input import SnapshotsConfigInput
from .storage_config_input import StorageConfigInput
from .summarize_descriptions_config_input import (
    SummarizeDescriptionsConfigInput,
)
from .text_embedding_config_input import TextEmbeddingConfigInput
from .umap_config_input import UmapConfigInput


class GraphRagConfigInput(LLMConfigInput):
    """Base class for the Default-Configuration parameterization settings."""

    reporting: NotRequired[ReportingConfigInput | None]
    storage: NotRequired[StorageConfigInput | None]
    cache: NotRequired[CacheConfigInput | None]
    input: NotRequired[InputConfigInput | None]
    embed_graph: NotRequired[EmbedGraphConfigInput | None]
    embeddings: NotRequired[TextEmbeddingConfigInput | None]
    chunks: NotRequired[ChunkingConfigInput | None]
    snapshots: NotRequired[SnapshotsConfigInput | None]
    entity_extraction: NotRequired[EntityExtractionConfigInput | None]
    summarize_descriptions: NotRequired[SummarizeDescriptionsConfigInput | None]
    community_reports: NotRequired[CommunityReportsConfigInput | None]
    claim_extraction: NotRequired[ClaimExtractionConfigInput | None]
    cluster_graph: NotRequired[ClusterGraphConfigInput | None]
    umap: NotRequired[UmapConfigInput | None]
    encoding_model: NotRequired[str | None]
    skip_workflows: NotRequired[list[str] | str | None]
    local_search: NotRequired[LocalSearchConfigInput | None]
    global_search: NotRequired[GlobalSearchConfigInput | None]
