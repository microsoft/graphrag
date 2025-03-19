# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from dataclasses import asdict
from pathlib import Path

from devtools import pformat
from pydantic import BaseModel, Field, model_validator

import graphrag.config.defaults as defs
from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.errors import LanguageModelConfigMissingError
from graphrag.config.models.basic_search_config import BasicSearchConfig
from graphrag.config.models.cache_config import CacheConfig
from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.config.models.cluster_graph_config import ClusterGraphConfig
from graphrag.config.models.community_reports_config import CommunityReportsConfig
from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.config.models.extract_claims_config import ClaimExtractionConfig
from graphrag.config.models.extract_graph_config import ExtractGraphConfig
from graphrag.config.models.extract_graph_nlp_config import ExtractGraphNLPConfig
from graphrag.config.models.global_search_config import GlobalSearchConfig
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
from graphrag.vector_stores.factory import VectorStoreType


class GraphRagConfig(BaseModel):
    """Base class for the Default-Configuration parameterization settings."""

    def __repr__(self) -> str:
        """Get a string representation."""
        return pformat(self, highlight=False)

    def __str__(self):
        """Get a string representation."""
        return self.model_dump_json(indent=4)

    root_dir: str = Field(
        description="The root directory for the configuration.",
        default=graphrag_config_defaults.root_dir,
    )

    def _validate_root_dir(self) -> None:
        """Validate the root directory."""
        if self.root_dir.strip() == "":
            self.root_dir = str(Path.cwd())

        root_dir = Path(self.root_dir).resolve()
        if not root_dir.is_dir():
            msg = f"Invalid root directory: {self.root_dir} is not a directory."
            raise FileNotFoundError(msg)
        self.root_dir = str(root_dir)

    models: dict[str, LanguageModelConfig] = Field(
        description="Available language model configurations.",
        default=graphrag_config_defaults.models,
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

    input: InputConfig = Field(
        description="The input configuration.", default=InputConfig()
    )
    """The input configuration."""

    def _validate_input_pattern(self) -> None:
        """Validate the input file pattern based on the specified type."""
        if len(self.input.file_pattern) == 0:
            if self.input.file_type == defs.InputFileType.text:
                self.input.file_pattern = ".*\\.txt$"
            else:
                self.input.file_pattern = f".*\\.{self.input.file_type.value}$"

    chunks: ChunkingConfig = Field(
        description="The chunking configuration to use.",
        default=ChunkingConfig(),
    )
    """The chunking configuration to use."""

    output: OutputConfig = Field(
        description="The output configuration.",
        default=OutputConfig(),
    )
    """The output configuration."""

    def _validate_output_base_dir(self) -> None:
        """Validate the output base directory."""
        if self.output.type == defs.OutputType.file:
            if self.output.base_dir.strip() == "":
                msg = "output base directory is required for file output. Please rerun `graphrag init` and set the output configuration."
                raise ValueError(msg)
            self.output.base_dir = str(
                (Path(self.root_dir) / self.output.base_dir).resolve()
            )

    outputs: dict[str, OutputConfig] | None = Field(
        description="A list of output configurations used for multi-index query.",
        default=graphrag_config_defaults.outputs,
    )

    def _validate_multi_output_base_dirs(self) -> None:
        """Validate the outputs dict base directories."""
        if self.outputs:
            for output in self.outputs.values():
                if output.type == defs.OutputType.file:
                    if output.base_dir.strip() == "":
                        msg = "Output base directory is required for file output. Please rerun `graphrag init` and set the output configuration."
                        raise ValueError(msg)
                    output.base_dir = str(
                        (Path(self.root_dir) / output.base_dir).resolve()
                    )

    update_index_output: OutputConfig = Field(
        description="The output configuration for the updated index.",
        default=OutputConfig(
            type=graphrag_config_defaults.update_index_output.type,
            base_dir=graphrag_config_defaults.update_index_output.base_dir,
        ),
    )
    """The output configuration for the updated index."""

    def _validate_update_index_output_base_dir(self) -> None:
        """Validate the update index output base directory."""
        if self.update_index_output.type == defs.OutputType.file:
            if self.update_index_output.base_dir.strip() == "":
                msg = "update_index_output base directory is required for file output. Please rerun `graphrag init` and set the update_index_output configuration."
                raise ValueError(msg)
            self.update_index_output.base_dir = str(
                (Path(self.root_dir) / self.update_index_output.base_dir).resolve()
            )

    cache: CacheConfig = Field(
        description="The cache configuration.", default=CacheConfig()
    )
    """The cache configuration."""

    reporting: ReportingConfig = Field(
        description="The reporting configuration.", default=ReportingConfig()
    )
    """The reporting configuration."""

    def _validate_reporting_base_dir(self) -> None:
        """Validate the reporting base directory."""
        if self.reporting.type == defs.ReportingType.file:
            if self.reporting.base_dir.strip() == "":
                msg = "Reporting base directory is required for file reporting. Please rerun `graphrag init` and set the reporting configuration."
                raise ValueError(msg)
            self.reporting.base_dir = str(
                (Path(self.root_dir) / self.reporting.base_dir).resolve()
            )

    vector_store: dict[str, VectorStoreConfig] = Field(
        description="The vector store configuration.",
        default_factory=lambda: {
            k: VectorStoreConfig(**asdict(v))
            for k, v in graphrag_config_defaults.vector_store.items()
        },
    )
    """The vector store configuration."""

    workflows: list[str] | None = Field(
        description="List of workflows to run, in execution order. This always overrides any built-in workflow methods.",
        default=graphrag_config_defaults.workflows,
    )
    """List of workflows to run, in execution order."""

    embed_text: TextEmbeddingConfig = Field(
        description="Text embedding configuration.",
        default=TextEmbeddingConfig(),
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

    extract_claims: ClaimExtractionConfig = Field(
        description="The claim extraction configuration to use.",
        default=ClaimExtractionConfig(
            enabled=graphrag_config_defaults.extract_claims.enabled,
        ),
    )
    """The claim extraction configuration to use."""

    community_reports: CommunityReportsConfig = Field(
        description="The community reports configuration to use.",
        default=CommunityReportsConfig(),
    )
    """The community reports configuration to use."""

    embed_graph: EmbedGraphConfig = Field(
        description="Graph embedding configuration.",
        default=EmbedGraphConfig(),
    )
    """Graph Embedding configuration."""

    umap: UmapConfig = Field(
        description="The UMAP configuration to use.", default=UmapConfig()
    )
    """The UMAP configuration to use."""

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

    def _validate_vector_store_db_uri(self) -> None:
        """Validate the vector store configuration."""
        for store in self.vector_store.values():
            if store.type == VectorStoreType.LanceDB:
                if not store.db_uri or store.db_uri.strip == "":
                    msg = "Vector store URI is required for LanceDB. Please rerun `graphrag init` and set the vector store configuration."
                    raise ValueError(msg)
                store.db_uri = str((Path(self.root_dir) / store.db_uri).resolve())

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
            err_msg = f"Model ID {model_id} not found in configuration. Please rerun `graphrag init` and set the model configuration."
            raise ValueError(err_msg)

        return self.models[model_id]

    def get_vector_store_config(self, vector_store_id: str) -> VectorStoreConfig:
        """Get a vector store configuration by ID.

        Parameters
        ----------
        vector_store_id : str
            The ID of the vector store to get. Should match an ID in the vector_store list.

        Returns
        -------
        VectorStoreConfig
            The vector store configuration if found.

        Raises
        ------
        ValueError
            If the vector store ID is not found in the configuration.
        """
        if vector_store_id not in self.vector_store:
            err_msg = f"Vector Store ID {vector_store_id} not found in configuration. Please rerun `graphrag init` and set the vector store configuration."
            raise ValueError(err_msg)

        return self.vector_store[vector_store_id]

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the model configuration."""
        self._validate_root_dir()
        self._validate_models()
        self._validate_input_pattern()
        self._validate_reporting_base_dir()
        self._validate_output_base_dir()
        self._validate_multi_output_base_dirs()
        self._validate_update_index_output_base_dir()
        self._validate_vector_store_db_uri()
        return self
