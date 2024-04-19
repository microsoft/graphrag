# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from .cache_config_input_model import CacheConfigInputModel
from .chunking_config_input_model import ChunkingConfigInputModel
from .claim_extraction_config_input_model import ClaimExtractionConfigInputModel
from .cluster_graph_config_input_model import ClusterGraphConfigInputModel
from .community_reports_config_input_model import CommunityReportsConfigInputModel
from .embed_graph_config_input_model import EmbedGraphConfigInputModel
from .entity_extraction_config_input_model import EntityExtractionConfigInputModel
from .input_config_input_model import InputConfigInputModel
from .llm_config_input_model import LLMConfigInputModel
from .reporting_config_input_model import ReportingConfigInputModel
from .snapshots_config_input_model import SnapshotsConfigInputModel
from .storage_config_input_model import StorageConfigInputModel
from .summarize_descriptions_config_input_model import (
    SummarizeDescriptionsConfigInputModel,
)
from .text_embedding_config_input_model import TextEmbeddingConfigInputModel
from .umap_config_input_model import UmapConfigInputModel


class DefaultConfigParametersInputModel(LLMConfigInputModel):
    """Base class for the Default-Configuration parameterization settings."""

    reporting: NotRequired[ReportingConfigInputModel | None]
    storage: NotRequired[StorageConfigInputModel | None]
    cache: NotRequired[CacheConfigInputModel | None]
    input: NotRequired[InputConfigInputModel | None]
    embed_graph: NotRequired[EmbedGraphConfigInputModel | None]
    embeddings: NotRequired[TextEmbeddingConfigInputModel | None]
    chunks: NotRequired[ChunkingConfigInputModel | None]
    snapshots: NotRequired[SnapshotsConfigInputModel | None]
    entity_extraction: NotRequired[EntityExtractionConfigInputModel | None]
    summarize_descriptions: NotRequired[SummarizeDescriptionsConfigInputModel | None]
    community_reports: NotRequired[CommunityReportsConfigInputModel | None]
    claim_extraction: NotRequired[ClaimExtractionConfigInputModel | None]
    cluster_graph: NotRequired[ClusterGraphConfigInputModel | None]
    umap: NotRequired[UmapConfigInputModel | None]
    encoding_model: NotRequired[str | None]
    skip_workflows: NotRequired[list[str] | str | None]
