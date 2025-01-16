# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from devtools import pformat
from pydantic import BaseModel, Field, model_validator

import graphrag.config.defaults as defs
from graphrag.config.errors import LanguageModelConfigMissingError
from graphrag.config.models.basic_search_config import BasicSearchConfig
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
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.config.models.local_search_config import LocalSearchConfig
from graphrag.config.models.reporting_config import ReportingConfig
from graphrag.config.models.snapshots_config import SnapshotsConfig
from graphrag.config.models.storage_config import StorageConfig
from graphrag.config.models.summarize_descriptions_config import (
    SummarizeDescriptionsConfig,
)
from graphrag.config.models.text_embedding_config import TextEmbeddingConfig
from graphrag.config.models.umap_config import UmapConfig


class GraphRagConfig(BaseModel):
    """Base class for the Default-Configuration parameterization settings."""

    def __repr__(self) -> str:
        """Get a string representation."""
        return pformat(self, highlight=False)

    def __str__(self):
        """Get a string representation."""
        return self.model_dump_json(indent=4)

    root_dir: str = Field(
        description="The root directory for the configuration.", default=""
    )

    def _validate_root_dir(self) -> None:
        """Validate the root directory."""
        if self.root_dir.strip() == "":
            self.root_dir = str(Path.cwd().resolve())

        if not Path(self.root_dir).is_dir():
            msg = f"Invalid root directory: {self.root_dir} is not a directory."
            raise FileNotFoundError(msg)

    models: dict[str, LanguageModelConfig] = Field(
        description="Available language model configurations.",
        default={
            defs.DEFAULT_CHAT_MODEL_ID: LanguageModelConfig.model_construct(
                model=defs.LLM_MODEL, type=defs.LLM_TYPE
            ),
            defs.DEFAULT_EMBEDDING_MODEL_ID: LanguageModelConfig.model_construct(
                model=defs.LLM_MODEL, type=defs.LLM_TYPE
            ),
        },
    )

    def _validate_models(self) -> None:
        """Validate the models configuration.

        Ensure both a default chat model and default embedding model
        have been defined. Other models may also be defined but
        defaults are required for the time being as places of the
        code fallback to default model configs instead
        of specifying a specific model.

        TODO: Don't fallback to default models elsewhere in the code.
        Forcing code to specify a model to use and allowing for any
        names for model configurations.
        """
        if defs.DEFAULT_CHAT_MODEL_ID not in self.models:
            raise LanguageModelConfigMissingError(defs.DEFAULT_CHAT_MODEL_ID)
        if defs.DEFAULT_EMBEDDING_MODEL_ID not in self.models:
            raise LanguageModelConfigMissingError(defs.DEFAULT_EMBEDDING_MODEL_ID)

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

    basic_search: BasicSearchConfig = Field(
        description="The basic search configuration.", default=BasicSearchConfig()
    )
    """The basic search configuration."""

    def get_language_model_config(self, model_id: str) -> LanguageModelConfig:
        """Get a model configuration by ID.

        Parameters
        ----------
        model_id : str
            The ID of the model to get. Should match an ID in the models list.

        Returns
        -------
        LanguageModelConfig
            The model configuration if found.

        Raises
        ------
        ValueError
            If the model ID is not found in the configuration.
        """
        if model_id not in self.models:
            err_msg = f"Model ID {model_id} not found in configuration."
            raise ValueError(err_msg)

        return self.models[model_id]

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the model configuration."""
        self._validate_root_dir()
        self._validate_models()
        return self
