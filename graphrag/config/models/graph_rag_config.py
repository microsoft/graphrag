# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from devtools import pformat
from pydantic import Field

import graphrag.config.defaults as defs
from graphrag.config.models.cache_config import CacheConfig
from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.config.models.claim_extraction_config import ClaimExtractionConfig
from graphrag.config.models.cluster_graph_config import ClusterGraphConfig
from graphrag.config.models.community_reports_config import CommunityReportsConfig
from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.config.models.entity_extraction_config import EntityExtractionConfig
from graphrag.config.models.global_search_config import GlobalSearchConfig
from graphrag.config.models.input_config import InputConfig
from graphrag.config.models.llm_config import LLMConfig
from graphrag.config.models.local_search_config import LocalSearchConfig
from graphrag.config.models.reporting_config import ReportingConfig
from graphrag.config.models.snapshots_config import SnapshotsConfig
from graphrag.config.models.storage_config import StorageConfig
from graphrag.config.models.summarize_descriptions_config import (
    SummarizeDescriptionsConfig,
)
from graphrag.config.models.text_embedding_config import TextEmbeddingConfig
from graphrag.config.models.umap_config import UmapConfig


class GraphRagConfig(LLMConfig):
    """Base class for the Default-Configuration parameterization settings."""

    def __repr__(self) -> str:
        """Get a string representation."""
        return pformat(self, highlight=False)

    def __str__(self):
        """Get a string representation."""
        return self.model_dump_json(indent=4)

    root_dir: str = Field(
        description="The root directory for the configuration.", default=None
    )

    reporting: ReportingConfig = Field(
        description="The reporting configuration.", default=ReportingConfig()
    )
    """The reporting configuration."""

    storage: StorageConfig = Field(
        description="The storage configuration.", default=StorageConfig()
    )
    """The storage configuration."""

    update_index_storage: StorageConfig | None = Field(
        description="The storage configuration for the updated index.",
        default=None,
    )
    """The storage configuration for the updated index."""

    cache: CacheConfig = Field(
        description="The cache configuration.", default=CacheConfig()
    )
    """The cache configuration."""

    input: InputConfig = Field(
        description="The input configuration.", default=InputConfig()
    )
    """The input configuration."""

    embed_graph: EmbedGraphConfig = Field(
        description="Graph embedding configuration.",
        default=EmbedGraphConfig(),
    )
    """Graph Embedding configuration."""

    embeddings: TextEmbeddingConfig = Field(
        description="The embeddings LLM configuration to use.",
        default=TextEmbeddingConfig(),
    )
    """The embeddings LLM configuration to use."""

    chunks: ChunkingConfig = Field(
        description="The chunking configuration to use.",
        default=ChunkingConfig(),
    )
    """The chunking configuration to use."""

    snapshots: SnapshotsConfig = Field(
        description="The snapshots configuration to use.",
        default=SnapshotsConfig(),
    )
    """The snapshots configuration to use."""

    entity_extraction: EntityExtractionConfig = Field(
        description="The entity extraction configuration to use.",
        default=EntityExtractionConfig(),
    )
    """The entity extraction configuration to use."""

    summarize_descriptions: SummarizeDescriptionsConfig = Field(
        description="The description summarization configuration to use.",
        default=SummarizeDescriptionsConfig(),
    )
    """The description summarization configuration to use."""

    community_reports: CommunityReportsConfig = Field(
        description="The community reports configuration to use.",
        default=CommunityReportsConfig(),
    )
    """The community reports configuration to use."""

    claim_extraction: ClaimExtractionConfig = Field(
        description="The claim extraction configuration to use.",
        default=ClaimExtractionConfig(
            enabled=defs.CLAIM_EXTRACTION_ENABLED,
        ),
    )
    """The claim extraction configuration to use."""

    cluster_graph: ClusterGraphConfig = Field(
        description="The cluster graph configuration to use.",
        default=ClusterGraphConfig(),
    )
    """The cluster graph configuration to use."""

    umap: UmapConfig = Field(
        description="The UMAP configuration to use.", default=UmapConfig()
    )
    """The UMAP configuration to use."""

    local_search: LocalSearchConfig = Field(
        description="The local search configuration.", default=LocalSearchConfig()
    )
    """The local search configuration."""

    global_search: GlobalSearchConfig = Field(
        description="The global search configuration.", default=GlobalSearchConfig()
    )
    """The global search configuration."""

    drift_search: DRIFTSearchConfig = Field(
        description="The drift search configuration.", default=DRIFTSearchConfig()
    )
    """The drift search configuration."""

    encoding_model: str = Field(
        description="The encoding model to use.", default=defs.ENCODING_MODEL
    )
    """The encoding model to use."""

    skip_workflows: list[str] = Field(
        description="The workflows to skip, usually for testing reasons.", default=[]
    )
    """The workflows to skip, usually for testing reasons."""
