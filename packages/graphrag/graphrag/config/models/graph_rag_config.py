# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from dataclasses import asdict
from pathlib import Path

from devtools import pformat
from graphrag_cache import CacheConfig
from graphrag_storage import StorageConfig, StorageType
from pydantic import BaseModel, Field, model_validator

import graphrag.config.defaults as defs
from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import VectorStoreType
from graphrag.config.models.basic_search_config import BasicSearchConfig
from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.config.models.cluster_graph_config import ClusterGraphConfig
from graphrag.config.models.community_reports_config import CommunityReportsConfig
from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.config.models.embed_text_config import EmbedTextConfig
from graphrag.config.models.extract_claims_config import ExtractClaimsConfig
from graphrag.config.models.extract_graph_config import ExtractGraphConfig
from graphrag.config.models.extract_graph_nlp_config import ExtractGraphNLPConfig
from graphrag.config.models.global_search_config import GlobalSearchConfig
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.config.models.local_search_config import LocalSearchConfig
from graphrag.config.models.prune_graph_config import PruneGraphConfig
from graphrag.config.models.reporting_config import ReportingConfig
from graphrag.config.models.snapshots_config import SnapshotsConfig
from graphrag.config.models.summarize_descriptions_config import (
    SummarizeDescriptionsConfig,
)
from graphrag.config.models.vector_store_config import VectorStoreConfig
from graphrag.index.input.input_config import InputConfig
from graphrag.language_model.providers.litellm.services.rate_limiter.rate_limiter_factory import (
    RateLimiterFactory,
)
from graphrag.language_model.providers.litellm.services.retry.retry_factory import (
    RetryFactory,
)


class GraphRagConfig(BaseModel):
    """Base class for the Default-Configuration parameterization settings."""

    def __repr__(self) -> str:
        """Get a string representation."""
        return pformat(self, highlight=False)

    def __str__(self):
        """Get a string representation."""
        return self.model_dump_json(indent=4)

    models: dict[str, LanguageModelConfig] = Field(
        description="Available language model configurations.",
        default=graphrag_config_defaults.models,
    )

    def _validate_retry_services(self) -> None:
        """Validate the retry services configuration."""
        retry_factory = RetryFactory()

        for model_id, model in self.models.items():
            if model.retry_strategy != "none":
                if model.retry_strategy not in retry_factory:
                    msg = f"Retry strategy '{model.retry_strategy}' for model '{model_id}' is not registered. Available strategies: {', '.join(retry_factory.keys())}"
                    raise ValueError(msg)

                _ = retry_factory.create(
                    strategy=model.retry_strategy,
                    init_args={
                        "max_retries": model.max_retries,
                        "max_retry_wait": model.max_retry_wait,
                    },
                )

    def _validate_rate_limiter_services(self) -> None:
        """Validate the rate limiter services configuration."""
        rate_limiter_factory = RateLimiterFactory()

        for model_id, model in self.models.items():
            if model.rate_limit_strategy is not None:
                if model.rate_limit_strategy not in rate_limiter_factory:
                    msg = f"Rate Limiter strategy '{model.rate_limit_strategy}' for model '{model_id}' is not registered. Available strategies: {', '.join(rate_limiter_factory.keys())}"
                    raise ValueError(msg)

                rpm = (
                    model.requests_per_minute
                    if type(model.requests_per_minute) is int
                    else None
                )
                tpm = (
                    model.tokens_per_minute
                    if type(model.tokens_per_minute) is int
                    else None
                )
                if rpm is not None or tpm is not None:
                    _ = rate_limiter_factory.create(
                        strategy=model.rate_limit_strategy,
                        init_args={"rpm": rpm, "tpm": tpm},
                    )

    input: InputConfig = Field(
        description="The input configuration.", default=InputConfig()
    )
    """The input configuration."""

    def _validate_input_pattern(self) -> None:
        """Validate the input file pattern based on the specified type."""
        if len(self.input.file_pattern) == 0:
            if self.input.file_type == defs.InputFileType.Text:
                self.input.file_pattern = ".*\\.txt$"
            else:
                self.input.file_pattern = f".*\\.{self.input.file_type}$"

    def _validate_input_base_dir(self) -> None:
        """Validate the input base directory."""
        if self.input.storage.type == StorageType.File:
            if not self.input.storage.base_dir:
                msg = "input storage base directory is required for file input storage. Please rerun `graphrag init` and set the input storage configuration."
                raise ValueError(msg)
            self.input.storage.base_dir = str(
                Path(self.input.storage.base_dir).resolve()
            )

    chunks: ChunkingConfig = Field(
        description="The chunking configuration to use.",
        default=ChunkingConfig(),
    )
    """The chunking configuration to use."""

    output: StorageConfig = Field(
        description="The output configuration.",
        default=StorageConfig(
            base_dir=graphrag_config_defaults.output.base_dir,
        ),
    )
    """The output configuration."""

    def _validate_output_base_dir(self) -> None:
        """Validate the output base directory."""
        if self.output.type == StorageType.File:
            if not self.output.base_dir:
                msg = "output base directory is required for file output. Please rerun `graphrag init` and set the output configuration."
                raise ValueError(msg)
            self.output.base_dir = str(Path(self.output.base_dir).resolve())

    update_index_output: StorageConfig = Field(
        description="The output configuration for the updated index.",
        default=StorageConfig(
            base_dir=graphrag_config_defaults.update_index_output.base_dir,
        ),
    )
    """The output configuration for the updated index."""

    def _validate_update_index_output_base_dir(self) -> None:
        """Validate the update index output base directory."""
        if self.update_index_output.type == StorageType.File:
            if not self.update_index_output.base_dir:
                msg = "update_index_output base directory is required for file output. Please rerun `graphrag init` and set the update_index_output configuration."
                raise ValueError(msg)
            self.update_index_output.base_dir = str(
                Path(self.update_index_output.base_dir).resolve()
            )

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
        if self.reporting.type == defs.ReportingType.file:
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

    def _validate_vector_store_db_uri(self) -> None:
        """Validate the vector store configuration."""
        store = self.vector_store
        if store.type == VectorStoreType.LanceDB:
            if not store.db_uri or store.db_uri.strip == "":
                msg = "Vector store URI is required for LanceDB. Please rerun `graphrag init` and set the vector store configuration."
                raise ValueError(msg)
            store.db_uri = str(Path(store.db_uri).resolve())

    def _validate_factories(self) -> None:
        """Validate the factories used in the configuration."""
        self._validate_retry_services()
        self._validate_rate_limiter_services()

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

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the model configuration."""
        self._validate_input_pattern()
        self._validate_input_base_dir()
        self._validate_reporting_base_dir()
        self._validate_output_base_dir()
        self._validate_update_index_output_base_dir()
        self._validate_vector_store_db_uri()
        self._validate_factories()
        return self
