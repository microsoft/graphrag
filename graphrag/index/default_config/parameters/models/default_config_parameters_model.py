# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import Field

from graphrag.index.default_config.parameters.defaults import DEFAULT_ENCODING_MODEL

from .cache_config_model import CacheConfigModel
from .chunking_config_model import ChunkingConfigModel
from .claim_extraction_config_model import ClaimExtractionConfigModel
from .cluster_graph_config_model import ClusterGraphConfigModel
from .community_reports_config_model import CommunityReportsConfigModel
from .embed_graph_config_model import EmbedGraphConfigModel
from .entity_extraction_config_model import EntityExtractionConfigModel
from .input_config_model import InputConfigModel
from .llm_config_model import LLMConfigModel
from .reporting_config_model import ReportingConfigModel
from .snapshots_config_model import SnapshotsConfigModel
from .storage_config_model import StorageConfigModel
from .summarize_descriptions_config_model import (
    SummarizeDescriptionsConfigModel,
)
from .text_embedding_config_model import TextEmbeddingConfigModel
from .umap_config_model import UmapConfigModel


class DefaultConfigParametersModel(LLMConfigModel):
    """Base class for the Default-Configuration parameterization settings."""

    root_dir: str = Field(
        description="The root directory for the configuration.", default=None
    )

    reporting: ReportingConfigModel = Field(
        description="The reporting configuration.", default=ReportingConfigModel()
    )
    """The reporting configuration."""

    storage: StorageConfigModel = Field(
        description="The storage configuration.", default=StorageConfigModel()
    )
    """The storage configuration."""

    cache: CacheConfigModel = Field(
        description="The cache configuration.", default=CacheConfigModel()
    )
    """The cache configuration."""

    input: InputConfigModel = Field(
        description="The input configuration.", default=InputConfigModel()
    )
    """The input configuration."""

    embed_graph: EmbedGraphConfigModel = Field(
        description="Graph embedding configuration.",
        default=EmbedGraphConfigModel(),
    )
    """Graph Embedding configuration."""

    embeddings: TextEmbeddingConfigModel = Field(
        description="The embeddings LLM configuration to use.",
        default=TextEmbeddingConfigModel(),
    )
    """The embeddings LLM configuration to use."""

    chunks: ChunkingConfigModel = Field(
        description="The chunking configuration to use.",
        default=ChunkingConfigModel(),
    )
    """The chunking configuration to use."""

    snapshots: SnapshotsConfigModel = Field(
        description="The snapshots configuration to use.",
        default=SnapshotsConfigModel(),
    )
    """The snapshots configuration to use."""

    entity_extraction: EntityExtractionConfigModel = Field(
        description="The entity extraction configuration to use.",
        default=EntityExtractionConfigModel(),
    )
    """The entity extraction configuration to use."""

    summarize_descriptions: SummarizeDescriptionsConfigModel = Field(
        description="The description summarization configuration to use.",
        default=SummarizeDescriptionsConfigModel(),
    )
    """The description summarization configuration to use."""

    community_reports: CommunityReportsConfigModel = Field(
        description="The community reports configuration to use.",
        default=CommunityReportsConfigModel(),
    )
    """The community reports configuration to use."""

    claim_extraction: ClaimExtractionConfigModel = Field(
        description="The claim extraction configuration to use.",
        default=ClaimExtractionConfigModel(),
    )
    """The claim extraction configuration to use."""

    cluster_graph: ClusterGraphConfigModel = Field(
        description="The cluster graph configuration to use.",
        default=ClusterGraphConfigModel(),
    )
    """The cluster graph configuration to use."""

    umap: UmapConfigModel = Field(
        description="The UMAP configuration to use.", default=UmapConfigModel()
    )
    """The UMAP configuration to use."""

    encoding_model: str = Field(
        description="The encoding model to use.", default=DEFAULT_ENCODING_MODEL
    )
    """The encoding model to use."""

    skip_workflows: list[str] = Field(
        description="The workflows to skip, usually for testing reasons.", default=[]
    )
    """The workflows to skip, usually for testing reasons."""
