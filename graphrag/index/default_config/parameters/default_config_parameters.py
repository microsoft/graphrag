# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from .models.default_config_parameters_model import DefaultConfigParametersModel
from .sections import (
    CacheConfigSection,
    ChunkingConfigSection,
    ClaimExtractionConfigSection,
    ClusterGraphConfigSection,
    CommunityReportsConfigSection,
    EmbedGraphConfigSection,
    EntityExtractionConfigSection,
    InputConfigSection,
    LLMConfigSection,
    ReportingConfigSection,
    SnapshotsConfigSection,
    StorageConfigSection,
    SummarizeDescriptionsConfigSection,
    TextEmbeddingConfigSection,
    UmapConfigSection,
)


class DefaultConfigParametersDict(LLMConfigSection):
    """Default-Configuration parameterization settings, loaded from environment variables."""

    _values: DefaultConfigParametersModel
    _root_dir: str
    _embed_graph: EmbedGraphConfigSection
    _reporting: ReportingConfigSection
    _storage: StorageConfigSection
    _cache: CacheConfigSection
    _input: InputConfigSection
    _embeddings: TextEmbeddingConfigSection
    _chunks: ChunkingConfigSection
    _snapshots: SnapshotsConfigSection
    _entity_extraction: EntityExtractionConfigSection
    _claim_extraction: ClaimExtractionConfigSection
    _cluster_graph: ClusterGraphConfigSection
    _umap: UmapConfigSection
    _community_reports: CommunityReportsConfigSection
    _summarize_descriptions: SummarizeDescriptionsConfigSection
    _summarize_documents: LLMConfigSection

    def __init__(
        self,
        values: DefaultConfigParametersModel,
        env: Env,
        root_dir: str,
    ):
        """Create a new instance of the parameters class."""
        super().__init__(values, values, env)
        root_dir = root_dir
        self._values = values
        self._root_dir = root_dir
        self._embed_graph = EmbedGraphConfigSection(values.embed_graph, env)
        self._reporting = ReportingConfigSection(values.reporting, env)
        self._storage = StorageConfigSection(values.storage, env)
        self._cache = CacheConfigSection(values.cache, env)
        self._input = InputConfigSection(values.input, env)
        self._embeddings = TextEmbeddingConfigSection(
            values.embeddings,
            values,
            self.encoding_model,
            env,
        )
        self._chunks = ChunkingConfigSection(values.chunks, self.encoding_model, env)
        self._snapshots = SnapshotsConfigSection(values.snapshots, env)
        self._entity_extraction = EntityExtractionConfigSection(
            values.entity_extraction,
            values,
            root_dir,
            self.encoding_model,
            env,
        )
        self._claim_extraction = ClaimExtractionConfigSection(
            values.claim_extraction, values, root_dir, env
        )
        self._cluster_graph = ClusterGraphConfigSection(values.cluster_graph, env)
        self._umap = UmapConfigSection(values.umap, env)
        self._community_reports = CommunityReportsConfigSection(
            values.community_reports, values, root_dir, env
        )
        self._summarize_descriptions = SummarizeDescriptionsConfigSection(
            values.summarize_descriptions, values, root_dir, env
        )

    @property
    def reporting(self) -> ReportingConfigSection:
        """The reporting configuration."""
        return self._reporting

    @property
    def embed_graph(self) -> EmbedGraphConfigSection:
        """A flag indicating whether to enable embed_graph."""
        return self._embed_graph

    @property
    def storage(self) -> StorageConfigSection:
        """The storage configuration."""
        return self._storage

    @property
    def cache(self) -> CacheConfigSection:
        """The cache config."""
        return self._cache

    @property
    def input(self) -> InputConfigSection:
        """The input configuration."""
        return self._input

    @property
    def embeddings(self) -> TextEmbeddingConfigSection:
        """The embeddings LLM configuration to use."""
        return self._embeddings

    @property
    def chunks(self) -> ChunkingConfigSection:
        """The chunking configuration."""
        return self._chunks

    @property
    def snapshots(self) -> SnapshotsConfigSection:
        """The snapshots configuration."""
        return self._snapshots

    @property
    def entity_extraction(self) -> EntityExtractionConfigSection:
        """The entity extraction configuration."""
        return self._entity_extraction

    @property
    def claim_extraction(self) -> ClaimExtractionConfigSection:
        """The claim extraction configuration."""
        return self._claim_extraction

    @property
    def cluster_graph(self) -> ClusterGraphConfigSection:
        """The cluster graph configuration."""
        return self._cluster_graph

    @property
    def umap(self) -> UmapConfigSection:
        """The UMAP configuration."""
        return self._umap

    @property
    def community_reports(self) -> CommunityReportsConfigSection:
        """The community reports configuration."""
        return self._community_reports

    @property
    def summarize_descriptions(self) -> SummarizeDescriptionsConfigSection:
        """The summarize descriptions configuration."""
        return self._summarize_descriptions

    @property
    def encoding_model(self) -> str:
        """The encoding model to use."""
        # cl100k_base for gpt3.5-turbo and gpt-4, https://github.com/openai/openai-cookbook/blob/63f95154b1a736b6c3e4834434b4077d110dd97a/examples/How_to_count_tokens_with_tiktoken.ipynb
        return self.replace(self._values.encoding_model, "cl100k_base")

    @property
    def root_dir(self) -> str:
        """The root directory of the pipeline."""
        return self._root_dir

    @property
    def skip_workflows(self) -> list[str]:
        """The workflows to skip, usually for testing reasons."""
        return self.replace(self._values.skip_workflows, [])

    def to_dict(self) -> dict:
        """Return a JSON representation of the parameters."""
        return {
            "root_dir": self.root_dir,
            "skip_workflows": self.skip_workflows,
            "encoding_model": self.encoding_model,
            "summarize_descriptions": self.summarize_descriptions.to_dict(),
            "community_reports": self.community_reports.to_dict(),
            "umap": self.umap.to_dict(),
            "cluster_graph": self.cluster_graph.to_dict(),
            "claim_extraction": self.claim_extraction.to_dict(),
            "entity_extraction": self.entity_extraction.to_dict(),
            "snapshots": self.snapshots.to_dict(),
            "chunks": self.chunks.to_dict(),
            "embeddings": self.embeddings.to_dict(),
            "input": self.input.to_dict(),
            "cache": self.cache.to_dict(),
            "storage": self.storage.to_dict(),
            "reporting": self.reporting.to_dict(),
            "embed_graph": self.embed_graph.to_dict(),
            **super().to_dict(),
        }
