import os
import unittest
from unittest import mock

import yaml

from graphrag.index import (
    CacheConfigModel,
    ChunkingConfigModel,
    ClaimExtractionConfigModel,
    ClusterGraphConfigModel,
    CommunityReportsConfigModel,
    DefaultConfigParametersModel,
    EmbedGraphConfigModel,
    EntityExtractionConfigModel,
    InputConfigModel,
    LLMParametersModel,
    PipelineCacheType,
    PipelineInputType,
    PipelineReportingType,
    PipelineStorageType,
    ReportingConfigModel,
    SnapshotsConfigModel,
    StorageConfigModel,
    SummarizeDescriptionsConfigModel,
    TextEmbeddingConfigModel,
    UmapConfigModel,
    default_config,
    default_config_parameters,
    default_config_parameters_from_env_vars,
)
from graphrag.index.config import (
    PipelineCSVInputConfig,
    PipelineTextInputConfig,
)

current_dir = os.path.dirname(__file__)


class TestDefaultConfig(unittest.TestCase):
    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_csv_input_returns_correct_config(self):
        config = default_config(default_config_parameters_from_env_vars("/some/root"))
        assert config.root_dir == "/some/root"

        # Make sure the input is a CSV input
        assert isinstance(config.input, PipelineCSVInputConfig)
        assert (config.input.file_pattern or "") == ".*\\.csv$"  # type: ignore

    @mock.patch.dict(
        os.environ,
        {"GRAPHRAG_API_KEY": "test", "GRAPHRAG_INPUT_TYPE": "text"},
        clear=True,
    )
    def test_text_input_returns_correct_config(self):
        os.environ["GRAPHRAG_INPUT_TYPE"] = "text"

        config = default_config(default_config_parameters_from_env_vars("."))
        assert isinstance(config.input, PipelineTextInputConfig)
        assert config.input is not None
        assert (config.input.file_pattern or "") == ".*\\.txt$"  # type: ignore

    @mock.patch.dict(
        os.environ,
        {
            "GRAPHRAG_API_KEY": "test",
            "GRAPHRAG_LLM_MODEL": "gpt2",
            "GRAPHRAG_THREAD_COUNT": "987",
            "GRAPHRAG_STORAGE_TYPE": "blob",
            "GRAPHRAG_STORAGE_CONNECTION_STRING": "test_cs",
            "GRAPHRAG_STORAGE_CONTAINER_NAME": "test_cn",
            "GRAPHRAG_CACHE_TYPE": "blob",
            "GRAPHRAG_CACHE_CONNECTION_STRING": "test_cs1",
            "GRAPHRAG_CACHE_CONTAINER_NAME": "test_cn1",
            "GRAPHRAG_REPORTING_TYPE": "blob",
            "GRAPHRAG_REPORTING_CONNECTION_STRING": "test_cs2",
            "GRAPHRAG_REPORTING_CONTAINER_NAME": "test_cn2",
            "GRAPHRAG_INPUT_TYPE": "text",
            "GRAPHRAG_INPUT_ENCODING": "utf-16",
            "GRAPHRAG_INPUT_DOCUMENT_ATTRIBUTE_COLUMNS": "test1,test2",
            "GRAPHRAG_NODE2VEC_NUM_WALKS": "5000000",
            "GRAPHRAG_EMBEDDING_MODEL": "text-embedding-2",
            "GRAPHRAG_EMBEDDING_BATCH_SIZE": "1000000",
            "GRAPHRAG_EMBEDDING_THREAD_COUNT": "2345",
            "GRAPHRAG_CHUNK_SIZE": "500",
            "GRAPHRAG_CHUNK_OVERLAP": "12",
            "GRAPHRAG_CHUNK_BY_COLUMNS": "a,b",
            "GRAPHRAG_SNAPSHOT_GRAPHML": "true",
            "GRAPHRAG_ENTITY_EXTRACTION_MAX_GLEANINGS": "112",
            "GRAPHRAG_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH": "12345",
            "GRAPHRAG_COMMUNITY_REPORT_MAX_LENGTH": "23456",
            "GRAPHRAG_CLAIM_EXTRACTION_DESCRIPTION": "derp 123",
            "GRAPHRAG_MAX_CLUSTER_SIZE": "123",
            "GRAPHRAG_UMAP_ENABLED": "true",
            "GRAPHRAG_ENCODING_MODEL": "derp123",
            "GRAPHRAG_SKIP_WORKFLOWS": "a,b,c",
        },
        clear=True,
    )
    def test_create_parameters_from_env_vars(self) -> None:
        parameters = default_config_parameters_from_env_vars(".")
        assert parameters.llm["api_key"] == "test"
        assert parameters.llm["model"] == "gpt2"
        assert parameters.parallelization["num_threads"] == 987
        assert parameters.encoding_model == "derp123"
        assert parameters.skip_workflows == ["a", "b", "c"]
        assert parameters.storage.type == PipelineStorageType.blob
        assert parameters.storage.connection_string == "test_cs"
        assert parameters.storage.container_name == "test_cn"
        assert parameters.cache.type == PipelineCacheType.blob
        assert parameters.cache.connection_string == "test_cs1"
        assert parameters.cache.container_name == "test_cn1"
        assert parameters.reporting.type == PipelineReportingType.blob
        assert parameters.reporting.connection_string == "test_cs2"
        assert parameters.reporting.container_name == "test_cn2"
        assert parameters.input.type == PipelineInputType.text
        assert parameters.input.file_encoding == "utf-16"
        assert parameters.input.document_attribute_columns == ["test1", "test2"]
        assert parameters.embed_graph.num_walks == 5_000_000
        assert parameters.embeddings.batch_size == 1_000_000
        assert parameters.embeddings.parallelization["num_threads"] == 2345
        assert parameters.embeddings.llm["model"] == "text-embedding-2"
        assert parameters.chunks.size == 500
        assert parameters.chunks.overlap == 12
        assert parameters.chunks.group_by_columns == ["a", "b"]
        assert parameters.snapshots.graphml
        assert parameters.entity_extraction.max_gleanings == 112
        assert parameters.summarize_descriptions.max_length == 12345
        assert parameters.community_reports.max_length == 23456
        assert parameters.claim_extraction.description == "derp 123"
        assert parameters.cluster_graph.max_cluster_size == 123
        assert parameters.umap.enabled

    @mock.patch.dict(os.environ, {"API_KEY_X": "test"}, clear=True)
    def test_create_parameters(self) -> None:
        parameters = default_config_parameters(
            DefaultConfigParametersModel(
                llm=LLMParametersModel(api_key="${API_KEY_X}", model="gpt2"),
                storage=StorageConfigModel(
                    type=PipelineStorageType.blob,
                    connection_string="test_cs",
                    container_name="test_cn",
                ),
                cache=CacheConfigModel(
                    type=PipelineCacheType.blob,
                    connection_string="test_cs1",
                    container_name="test_cn1",
                ),
                reporting=ReportingConfigModel(
                    type=PipelineReportingType.blob,
                    connection_string="test_cs2",
                    container_name="test_cn2",
                ),
                input=InputConfigModel(
                    type=PipelineInputType.text,
                    file_encoding="utf-16",
                    document_attribute_columns=["test1", "test2"],
                ),
                embed_graph=EmbedGraphConfigModel(
                    num_walks=5_000_000,
                ),
                embeddings=TextEmbeddingConfigModel(
                    batch_size=1_000_000,
                    batch_max_tokens=8000,
                    skip=["a1", "b1", "c1"],
                    llm=LLMParametersModel(model="text-embedding-2"),
                ),
                chunks=ChunkingConfigModel(
                    size=500, overlap=12, group_by_columns=["a", "b"]
                ),
                snapshots=SnapshotsConfigModel(
                    graphml=True,
                ),
                entity_extraction=EntityExtractionConfigModel(max_gleanings=112),
                summarize_descriptions=SummarizeDescriptionsConfigModel(
                    max_length=12345,
                ),
                community_reports=CommunityReportsConfigModel(
                    max_length=23456,
                ),
                claim_extraction=ClaimExtractionConfigModel(description="derp 123"),
                cluster_graph=ClusterGraphConfigModel(
                    max_cluster_size=123,
                ),
                umap=UmapConfigModel(enabled=True),
                encoding_model="derp123",
                skip_workflows=["a", "b", "c"],
            ),
            ".",
        )
        assert parameters.llm["api_key"] == "test"
        assert parameters.llm["model"] == "gpt2"
        assert parameters.encoding_model == "derp123"
        assert parameters.skip_workflows == ["a", "b", "c"]
        assert parameters.storage.type == PipelineStorageType.blob
        assert parameters.storage.connection_string == "test_cs"
        assert parameters.storage.container_name == "test_cn"
        assert parameters.cache.type == PipelineCacheType.blob
        assert parameters.cache.connection_string == "test_cs1"
        assert parameters.cache.container_name == "test_cn1"
        assert parameters.reporting.type == PipelineReportingType.blob
        assert parameters.reporting.connection_string == "test_cs2"
        assert parameters.reporting.container_name == "test_cn2"
        assert parameters.input.type == PipelineInputType.text
        assert parameters.input.file_encoding == "utf-16"
        assert parameters.input.document_attribute_columns == ["test1", "test2"]
        assert parameters.embed_graph.num_walks == 5_000_000
        assert parameters.embeddings.batch_size == 1_000_000
        assert parameters.embeddings.batch_max_tokens == 8000
        assert parameters.embeddings.skip == ["a1", "b1", "c1"]
        assert parameters.embeddings.llm["model"] == "text-embedding-2"
        assert parameters.chunks.size == 500
        assert parameters.chunks.overlap == 12
        assert parameters.chunks.group_by_columns == ["a", "b"]
        assert parameters.snapshots.graphml
        assert parameters.entity_extraction.max_gleanings == 112
        assert parameters.summarize_descriptions.max_length == 12345
        assert parameters.community_reports.max_length == 23456
        assert parameters.claim_extraction.description == "derp 123"
        assert parameters.cluster_graph.max_cluster_size == 123
        assert parameters.umap.enabled


@mock.patch.dict(
    os.environ,
    {
        "PIPELINE_LLM_API_KEY": "test",
        "PIPELINE_LLM_API_BASE": "http://test",
        "PIPELINE_LLM_API_VERSION": "v1",
        "PIPELINE_LLM_MODEL": "gpt2",
        "PIPELINE_LLM_DEPLOYMENT_NAME": "test",
    },
    clear=True,
)
def test_yaml_load_e2e():
    config_dict = yaml.safe_load(
        """
input:
  type: text

llm:
  type: azure_openai_chat
  api_key: ${PIPELINE_LLM_API_KEY}
  api_base: ${PIPELINE_LLM_API_BASE}
  api_version: ${PIPELINE_LLM_API_VERSION}
  model: ${PIPELINE_LLM_MODEL}
  deployment_name: ${PIPELINE_LLM_DEPLOYMENT_NAME}
  model_supports_json: True
  tokens_per_minute: 80000
  requests_per_minute: 900
  thread_count: 50
  concurrent_requests: 25
"""
    )
    # create default configuration pipeline parameters from the custom settings
    model = DefaultConfigParametersModel.model_validate(config_dict)
    parameters = default_config_parameters(model, ".", None)

    assert parameters.llm["api_key"] == "test"
    assert parameters.llm["model"] == "gpt2"
    assert parameters.llm["api_base"] == "http://test"
    assert parameters.llm["api_version"] == "v1"
    assert parameters.llm["deployment_name"] == "test"

    # generate the pipeline from the default parameters
    pipeline_config = default_config(parameters, True)

    config_str = pipeline_config.model_dump_json()
    assert "${PIPELINE_LLM_API_KEY}" not in config_str
    assert "${PIPELINE_LLM_API_BASE}" not in config_str
    assert "${PIPELINE_LLM_API_VERSION}" not in config_str
    assert "${PIPELINE_LLM_MODEL}" not in config_str
    assert "${PIPELINE_LLM_DEPLOYMENT_NAME}" not in config_str
