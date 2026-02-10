# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from dataclasses import asdict
from pathlib import Path

from devtools import pformat
from graphrag_cache import CacheConfig
from graphrag_chunking.chunking_config import ChunkingConfig
from graphrag_input import InputConfig
from graphrag_llm.config import ModelConfig
from graphrag_storage import StorageConfig, StorageType
from graphrag_storage.tables.table_provider_config import TableProviderConfig
from graphrag_vectors import IndexSchema, VectorStoreConfig, VectorStoreType
from pydantic import BaseModel, Field, model_validator

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.embeddings import all_embeddings
from graphrag.config.enums import AsyncType, ReportingType
from graphrag.config.models.basic_search_config import BasicSearchConfig
from graphrag.config.models.cluster_graph_config import ClusterGraphConfig
from graphrag.config.models.community_reports_config import CommunityReportsConfig
from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.config.models.embed_text_config import EmbedTextConfig
from graphrag.config.models.extract_claims_config import ExtractClaimsConfig
from graphrag.config.models.extract_graph_config import ExtractGraphConfig
from graphrag.config.models.extract_graph_nlp_config import ExtractGraphNLPConfig
from graphrag.config.models.global_search_config import GlobalSearchConfig
from graphrag.config.models.local_search_config import LocalSearchConfig
from graphrag.config.models.prune_graph_config import PruneGraphConfig
from graphrag.config.models.reporting_config import ReportingConfig
from graphrag.config.models.snapshots_config import SnapshotsConfig
from graphrag.config.models.summarize_descriptions_config import (
    SummarizeDescriptionsConfig,
)


class GraphRagConfig(BaseModel):
    """Base class for the Default-Configuration parameterization settings."""

    def __repr__(self) -> str:
        """Get a string representation."""
        return pformat(self, highlight=False)

    def __str__(self):
        """Get a string representation."""
        return self.model_dump_json(indent=4)

    completion_models: dict[str, ModelConfig] = Field(
        description="Available completion model configurations.",
        default=graphrag_config_defaults.completion_models,
    )

    embedding_models: dict[str, ModelConfig] = Field(
        description="Available embedding model configurations.",
        default=graphrag_config_defaults.embedding_models,
    )

    concurrent_requests: int = Field(
        description="The default number of concurrent requests to make to language models.",
        default=graphrag_config_defaults.concurrent_requests,
    )

    async_mode: AsyncType = Field(
        description="The default asynchronous mode to use for language model requests.",
        default=graphrag_config_defaults.async_mode,
    )

    input: InputConfig = Field(
        description="The input configuration.", default=InputConfig()
    )
    """The input configuration."""

    input_storage: StorageConfig = Field(
        description="The input storage configuration.",
        default=StorageConfig(
            base_dir=graphrag_config_defaults.input_storage.base_dir,
        ),
    )
    """The input storage configuration."""

    def _validate_input_base_dir(self) -> None:
        """Validate the input base directory."""
        if self.input_storage.type == StorageType.File:
            if not self.input_storage.base_dir:
                msg = "input storage base directory is required for file input storage. Please rerun `graphrag init` and set the input storage configuration."
                raise ValueError(msg)
            self.input_storage.base_dir = str(
                Path(self.input_storage.base_dir).resolve()
            )

    chunking: ChunkingConfig = Field(
        description="The chunking configuration to use.",
        default=ChunkingConfig(
            type=graphrag_config_defaults.chunking.type,
            size=graphrag_config_defaults.chunking.size,
            overlap=graphrag_config_defaults.chunking.overlap,
            encoding_model=graphrag_config_defaults.chunking.encoding_model,
            prepend_metadata=graphrag_config_defaults.chunking.prepend_metadata,
        ),
    )
    """The chunking configuration to use."""

    output_storage: StorageConfig = Field(
        description="The output configuration.",
        default=StorageConfig(
            base_dir=graphrag_config_defaults.output_storage.base_dir,
        ),
    )
    """The output configuration."""

    def _validate_output_base_dir(self) -> None:
        """Validate the output base directory."""
        if self.output_storage.type == StorageType.File:
            if not self.output_storage.base_dir:
                msg = "output base directory is required for file output. Please rerun `graphrag init` and set the output configuration."
                raise ValueError(msg)
            self.output_storage.base_dir = str(
                Path(self.output_storage.base_dir).resolve()
            )

    update_output_storage: StorageConfig = Field(
        description="The output configuration for the updated index.",
        default=StorageConfig(
            base_dir=graphrag_config_defaults.update_output_storage.base_dir,
        ),
    )
    """The output configuration for the updated index."""

    def _validate_update_output_storage_base_dir(self) -> None:
        """Validate the update output base directory."""
        if self.update_output_storage.type == StorageType.File:
            if not self.update_output_storage.base_dir:
                msg = "update_output_storage base directory is required for file output. Please rerun `graphrag init` and set the update_output_storage configuration."
                raise ValueError(msg)
            self.update_output_storage.base_dir = str(
                Path(self.update_output_storage.base_dir).resolve()
            )

    table_provider: TableProviderConfig = Field(
        description="The table provider configuration.", default=TableProviderConfig()
    )
    """The table provider configuration. By default we read/write parquet to disk. You can register custom output table storage."""

    cache: CacheConfig = Field(
        description="The cache configuration.",
        default=CacheConfig(**asdict(graphrag_config_defaults.cache)),
    )
    """The cache configuration."""

    reporting: ReportingConfig = Field(
        description="The reporting configuration.", default=ReportingConfig()
    )
    """The reporting configuration."""

    def _validate_reporting_base_dir(self) -> None:
        """Validate the reporting base directory."""
        if self.reporting.type == ReportingType.file:
            if self.reporting.base_dir.strip() == "":
                msg = "Reporting base directory is required for file reporting. Please rerun `graphrag init` and set the reporting configuration."
                raise ValueError(msg)
            self.reporting.base_dir = str(Path(self.reporting.base_dir).resolve())

    vector_store: VectorStoreConfig = Field(
        description="The vector store configuration.", default=VectorStoreConfig()
    )
    """The vector store configuration."""

    workflows: list[str] | None = Field(
        description="List of workflows to run, in execution order. This always overrides any built-in workflow methods.",
        default=graphrag_config_defaults.workflows,
    )
    """List of workflows to run, in execution order."""

    embed_text: EmbedTextConfig = Field(
        description="Text embedding configuration.",
        default=EmbedTextConfig(),
    )
    """Text embedding configuration."""

    extract_graph: ExtractGraphConfig = Field(
        description="The entity extraction configuration to use.",
        default=ExtractGraphConfig(),
    )
    """The entity extraction configuration to use."""

    summarize_descriptions: SummarizeDescriptionsConfig = Field(
        description="The description summarization configuration to use.",
        default=SummarizeDescriptionsConfig(),
    )
    """The description summarization configuration to use."""

    extract_graph_nlp: ExtractGraphNLPConfig = Field(
        description="The NLP-based graph extraction configuration to use.",
        default=ExtractGraphNLPConfig(),
    )
    """The NLP-based graph extraction configuration to use."""

    prune_graph: PruneGraphConfig = Field(
        description="The graph pruning configuration to use.",
        default=PruneGraphConfig(),
    )
    """The graph pruning configuration to use."""

    cluster_graph: ClusterGraphConfig = Field(
        description="The cluster graph configuration to use.",
        default=ClusterGraphConfig(),
    )
    """The cluster graph configuration to use."""

    extract_claims: ExtractClaimsConfig = Field(
        description="The claim extraction configuration to use.",
        default=ExtractClaimsConfig(
            enabled=graphrag_config_defaults.extract_claims.enabled,
        ),
    )
    """The claim extraction configuration to use."""

    community_reports: CommunityReportsConfig = Field(
        description="The community reports configuration to use.",
        default=CommunityReportsConfig(),
    )
    """The community reports configuration to use."""

    snapshots: SnapshotsConfig = Field(
        description="The snapshots configuration to use.",
        default=SnapshotsConfig(),
    )
    """The snapshots configuration to use."""

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

    def _validate_vector_store(self) -> None:
        """Validate the vector store configuration specifically in the GraphRAG context. This checks and sets required dynamic defaults for the embeddings we require."""
        self._validate_vector_store_db_uri()
        # check and insert/overlay schemas for all of the core embeddings
        # note that this does not require that they are used, only that they have a schema
        # the embed_text block has the list of actual embeddings
        if not self.vector_store.index_schema:
            self.vector_store.index_schema = {}
        for embedding in all_embeddings:
            if embedding not in self.vector_store.index_schema:
                self.vector_store.index_schema[embedding] = IndexSchema(
                    index_name=embedding,
                )

    def _validate_vector_store_db_uri(self) -> None:
        """Validate the vector store configuration."""
        store = self.vector_store
        if store.type == VectorStoreType.LanceDB:
            if not store.db_uri or store.db_uri.strip == "":
                store.db_uri = graphrag_config_defaults.vector_store.db_uri
            store.db_uri = str(Path(store.db_uri).resolve())

    def get_completion_model_config(self, model_id: str) -> ModelConfig:
        """Get a completion model configuration by ID.

        Parameters
        ----------
        model_id : str
            The ID of the model to get. Should match an ID in the completion_models list.

        Returns
        -------
        ModelConfig
            The model configuration if found.

        Raises
        ------
        ValueError
            If the model ID is not found in the configuration.
        """
        if model_id not in self.completion_models:
            err_msg = f"Model ID {model_id} not found in completion_models. Please rerun `graphrag init` and set the completion_models configuration."
            raise ValueError(err_msg)

        return self.completion_models[model_id]

    def get_embedding_model_config(self, model_id: str) -> ModelConfig:
        """Get an embedding model configuration by ID.

        Parameters
        ----------
        model_id : str
            The ID of the model to get. Should match an ID in the embedding_models list.

        Returns
        -------
        ModelConfig
            The model configuration if found.

        Raises
        ------
        ValueError
            If the model ID is not found in the configuration.
        """
        if model_id not in self.embedding_models:
            err_msg = f"Model ID {model_id} not found in embedding_models. Please rerun `graphrag init` and set the embedding_models configuration."
            raise ValueError(err_msg)

        return self.embedding_models[model_id]

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the model configuration."""
        self._validate_input_base_dir()
        self._validate_reporting_base_dir()
        self._validate_output_base_dir()
        self._validate_update_output_storage_base_dir()
        self._validate_vector_store()
        return self
