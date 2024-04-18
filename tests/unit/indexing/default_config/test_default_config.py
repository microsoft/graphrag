# Copyright (c) 2024 Microsoft Corporation. All rights reserved.
import os
import re
import unittest
from pathlib import Path
from unittest import mock

import pytest
import yaml
from datashaper import AsyncType

from graphrag.index import (
    ApiKeyMissingError,
    AzureApiBaseMissingError,
    AzureDeploymentNameMissingError,
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

ALL_ENV_VARS = {
    "GRAPHRAG_API_BASE": "http://some/base",
    "GRAPHRAG_API_KEY": "test",
    "GRAPHRAG_API_ORGANIZATION": "test_org",
    "GRAPHRAG_API_PROXY": "http://some/proxy",
    "GRAPHRAG_API_VERSION": "v1234",
    "GRAPHRAG_ASYNC_MODE": "asyncio",
    "GRAPHRAG_CACHE_BASE_DIR": "/some/cache/dir",
    "GRAPHRAG_CACHE_CONNECTION_STRING": "test_cs1",
    "GRAPHRAG_CACHE_CONTAINER_NAME": "test_cn1",
    "GRAPHRAG_CACHE_TYPE": "blob",
    "GRAPHRAG_CHUNK_BY_COLUMNS": "a,b",
    "GRAPHRAG_CHUNK_OVERLAP": "12",
    "GRAPHRAG_CHUNK_SIZE": "500",
    "GRAPHRAG_CLAIM_EXTRACTION_DESCRIPTION": "test 123",
    "GRAPHRAG_CLAIM_EXTRACTION_MAX_GLEANINGS": "5000",
    "GRAPHRAG_CLAIM_EXTRACTION_PROMPT_FILE": "tests/unit/indexing/default_config/prompt-a.txt",
    "GRAPHRAG_COMMUNITY_REPORT_MAX_LENGTH": "23456",
    "GRAPHRAG_COMMUNITY_REPORT_PROMPT_FILE": "tests/unit/indexing/default_config/prompt-b.txt",
    "GRAPHRAG_EMBEDDING_BATCH_MAX_TOKENS": "17",
    "GRAPHRAG_EMBEDDING_BATCH_SIZE": "1000000",
    "GRAPHRAG_EMBEDDING_CONCURRENT_REQUESTS": "12",
    "GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME": "model-deployment-name",
    "GRAPHRAG_EMBEDDING_MAX_RETRIES": "3",
    "GRAPHRAG_EMBEDDING_MAX_RETRY_WAIT": "0.1123",
    "GRAPHRAG_EMBEDDING_MODEL": "text-embedding-2",
    "GRAPHRAG_EMBEDDING_RPM": "500",
    "GRAPHRAG_EMBEDDING_SKIP": "a1,b1,c1",
    "GRAPHRAG_EMBEDDING_SLEEP_ON_RATE_LIMIT_RECOMMENDATION": "False",
    "GRAPHRAG_EMBEDDING_TARGET": "all",
    "GRAPHRAG_EMBEDDING_THREAD_COUNT": "2345",
    "GRAPHRAG_EMBEDDING_THREAD_STAGGER": "0.456",
    "GRAPHRAG_EMBEDDING_TPM": "7000",
    "GRAPHRAG_EMBEDDING_TYPE": "azure_openai_embedding",
    "GRAPHRAG_ENCODING_MODEL": "test123",
    "GRAPHRAG_ENTITY_EXTRACTION_ENTITY_TYPES": "cat,dog,elephant",
    "GRAPHRAG_ENTITY_EXTRACTION_MAX_GLEANINGS": "112",
    "GRAPHRAG_ENTITY_EXTRACTION_PROMPT_FILE": "tests/unit/indexing/default_config/prompt-c.txt",
    "GRAPHRAG_INPUT_BASE_DIR": "/some/input/dir",
    "GRAPHRAG_INPUT_CONNECTION_STRING": "input_cs",
    "GRAPHRAG_INPUT_CONTAINER_NAME": "input_cn",
    "GRAPHRAG_INPUT_DOCUMENT_ATTRIBUTE_COLUMNS": "test1,test2",
    "GRAPHRAG_INPUT_ENCODING": "utf-16",
    "GRAPHRAG_INPUT_FILE_PATTERN": ".*\\test\\.txt$",
    "GRAPHRAG_INPUT_SOURCE_COLUMN": "test_source",
    "GRAPHRAG_INPUT_STORAGE_TYPE": "blob",
    "GRAPHRAG_INPUT_TEXT_COLUMN": "test_text",
    "GRAPHRAG_INPUT_TIMESTAMP_COLUMN": "test_timestamp",
    "GRAPHRAG_INPUT_TIMESTAMP_FORMAT": "test_format",
    "GRAPHRAG_INPUT_TITLE_COLUMN": "test_title",
    "GRAPHRAG_INPUT_TYPE": "text",
    "GRAPHRAG_LLM_CONCURRENT_REQUESTS": "12",
    "GRAPHRAG_LLM_DEPLOYMENT_NAME": "model-deployment-name-x",
    "GRAPHRAG_LLM_MAX_RETRIES": "312",
    "GRAPHRAG_LLM_MAX_RETRY_WAIT": "0.1122",
    "GRAPHRAG_LLM_MAX_TOKENS": "15000",
    "GRAPHRAG_LLM_MODEL_SUPPORTS_JSON": "true",
    "GRAPHRAG_LLM_MODEL": "test-llm",
    "GRAPHRAG_LLM_REQUEST_TIMEOUT": "12.7",
    "GRAPHRAG_LLM_RPM": "900",
    "GRAPHRAG_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION": "False",
    "GRAPHRAG_LLM_THREAD_COUNT": "987",
    "GRAPHRAG_LLM_THREAD_STAGGER": "0.123",
    "GRAPHRAG_LLM_TPM": "8000",
    "GRAPHRAG_LLM_TYPE": "azure_openai_chat",
    "GRAPHRAG_MAX_CLUSTER_SIZE": "123",
    "GRAPHRAG_NODE2VEC_ENABLED": "true",
    "GRAPHRAG_NODE2VEC_ITERATIONS": "878787",
    "GRAPHRAG_NODE2VEC_NUM_WALKS": "5000000",
    "GRAPHRAG_NODE2VEC_RANDOM_SEED": "010101",
    "GRAPHRAG_NODE2VEC_WALK_LENGTH": "555111",
    "GRAPHRAG_NODE2VEC_WINDOW_SIZE": "12345",
    "GRAPHRAG_REPORTING_BASE_DIR": "/some/reporting/dir",
    "GRAPHRAG_REPORTING_CONNECTION_STRING": "test_cs2",
    "GRAPHRAG_REPORTING_CONTAINER_NAME": "test_cn2",
    "GRAPHRAG_REPORTING_TYPE": "blob",
    "GRAPHRAG_SKIP_WORKFLOWS": "a,b,c",
    "GRAPHRAG_SNAPSHOT_GRAPHML": "true",
    "GRAPHRAG_SNAPSHOT_RAW_ENTITIES": "true",
    "GRAPHRAG_SNAPSHOT_TOP_LEVEL_NODES": "true",
    "GRAPHRAG_STORAGE_BASE_DIR": "/some/storage/dir",
    "GRAPHRAG_STORAGE_CONNECTION_STRING": "test_cs",
    "GRAPHRAG_STORAGE_CONTAINER_NAME": "test_cn",
    "GRAPHRAG_STORAGE_TYPE": "blob",
    "GRAPHRAG_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH": "12345",
    "GRAPHRAG_SUMMARIZE_DESCRIPTIONS_PROMPT_FILE": "tests/unit/indexing/default_config/prompt-d.txt",
    "GRAPHRAG_UMAP_ENABLED": "true",
}


class TestDefaultConfig(unittest.TestCase):
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_default_config_with_no_env_vars_throws(self):
        with pytest.raises(ApiKeyMissingError):
            # This should throw an error because the API key is missing
            default_config(default_config_parameters_from_env_vars("."))

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_default_config_with_api_key_passes(self):
        # doesn't throw
        config = default_config(default_config_parameters_from_env_vars("."))
        assert config is not None

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True)
    def test_default_config_with_oai_key_passes(self):
        # doesn't throw
        config = default_config(default_config_parameters_from_env_vars("."))
        assert config is not None

    @mock.patch.dict(
        os.environ,
        {
            "GRAPHRAG_API_KEY": "test",
            "GRAPHRAG_LLM_TYPE": "azure_openai_chat",
            "GRAPHRAG_LLM_DEPLOYMENT_NAME": "x",
        },
        clear=True,
    )
    def test_throws_if_azure_is_used_without_api_base(self):
        with pytest.raises(AzureApiBaseMissingError):
            default_config_parameters_from_env_vars(".")

    @mock.patch.dict(
        os.environ,
        {
            "GRAPHRAG_API_KEY": "test",
            "GRAPHRAG_LLM_TYPE": "azure_openai_chat",
            "GRAPHRAG_LLM_BASE": "http://some/base",
        },
        clear=True,
    )
    def test_throws_if_azure_is_used_without_llm_deployment_name(self):
        with pytest.raises(AzureDeploymentNameMissingError):
            default_config_parameters_from_env_vars(".")

    @mock.patch.dict(
        os.environ,
        {
            "GRAPHRAG_API_KEY": "test",
            "GRAPHRAG_LLM_TYPE": "azure_openai_chat",
            "GRAPHRAG_API_BASE": "http://some/base",
            "GRAPHRAG_LLM_DEPLOYMENT_NAME": "model-deployment-name-x",
            "GRAPHRAG_EMBEDDING_TYPE": "azure_openai_embedding",
        },
        clear=True,
    )
    def test_throws_if_azure_is_used_without_embedding_deployment_name(self):
        with pytest.raises(AzureDeploymentNameMissingError):
            default_config_parameters_from_env_vars(".")

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

    def test_all_env_vars_is_accurate(self):
        env_var_docs_path = Path("docsite/posts/config/env_vars.md")
        env_var_docs = env_var_docs_path.read_text(encoding="utf-8")

        def find_envvar_names(text):
            pattern = r"`(GRAPHRAG_[^`]+)`"
            return re.findall(pattern, text)

        env_var_docs_path = Path("docsite/posts/config/env_vars.md")
        env_var_docs = env_var_docs_path.read_text(encoding="utf-8")
        graphrag_strings = find_envvar_names(env_var_docs)

        missing = {
            s for s in graphrag_strings if s not in ALL_ENV_VARS and not s.endswith("_")
        }
        # Remove configs covered by the base LLM connection configs
        missing = missing - {
            "GRAPHRAG_LLM_API_KEY",
            "GRAPHRAG_LLM_API_BASE",
            "GRAPHRAG_LLM_API_VERSION",
            "GRAPHRAG_LLM_API_ORGANIZATION",
            "GRAPHRAG_LLM_API_PROXY",
            "GRAPHRAG_EMBEDDING_API_KEY",
            "GRAPHRAG_EMBEDDING_API_BASE",
            "GRAPHRAG_EMBEDDING_API_VERSION",
            "GRAPHRAG_EMBEDDING_API_ORGANIZATION",
            "GRAPHRAG_EMBEDDING_API_PROXY",
        }
        if missing:
            msg = f"{len(missing)} missing env vars: {missing}"
            print(msg)
            raise ValueError(msg)

    @mock.patch.dict(
        os.environ,
        ALL_ENV_VARS,
        clear=True,
    )
    def test_create_parameters_from_env_vars(self) -> None:
        parameters = default_config_parameters_from_env_vars(".")
        assert parameters.async_mode == AsyncType.AsyncIO
        assert parameters.cache.base_dir == "/some/cache/dir"
        assert parameters.cache.connection_string == "test_cs1"
        assert parameters.cache.container_name == "test_cn1"
        assert parameters.cache.type == PipelineCacheType.blob
        assert parameters.chunks.group_by_columns == ["a", "b"]
        assert parameters.chunks.overlap == 12
        assert parameters.chunks.size == 500
        assert parameters.claim_extraction.description == "test 123"
        assert parameters.claim_extraction.max_gleanings == 5000
        assert parameters.claim_extraction.prompt == "Hello, World! A"
        assert parameters.cluster_graph.max_cluster_size == 123
        assert parameters.community_reports.max_length == 23456
        assert parameters.community_reports.prompt == "Hello, World! B"
        assert parameters.embed_graph.enabled
        assert parameters.embed_graph.iterations == 878787
        assert parameters.embed_graph.num_walks == 5_000_000
        assert parameters.embed_graph.random_seed == 10101
        assert parameters.embed_graph.walk_length == 555111
        assert parameters.embed_graph.window_size == 12345
        assert parameters.embeddings.batch_max_tokens == 17
        assert parameters.embeddings.batch_size == 1_000_000
        assert parameters.embeddings.llm["concurrent_requests"] == 12
        assert parameters.embeddings.llm["deployment_name"] == "model-deployment-name"
        assert parameters.embeddings.llm["max_retries"] == 3
        assert parameters.embeddings.llm["max_retry_wait"] == 0.1123
        assert parameters.embeddings.llm["model"] == "text-embedding-2"
        assert parameters.embeddings.llm["requests_per_minute"] == 500
        assert parameters.embeddings.llm["sleep_on_rate_limit_recommendation"] is False
        assert parameters.embeddings.llm["tokens_per_minute"] == 7000
        assert parameters.embeddings.llm["type"] == "azure_openai_embedding"
        assert parameters.embeddings.parallelization["num_threads"] == 2345
        assert parameters.embeddings.parallelization["stagger"] == 0.456
        assert parameters.embeddings.skip == ["a1", "b1", "c1"]
        assert parameters.embeddings.target == "all"
        assert parameters.encoding_model == "test123"
        assert parameters.entity_extraction.entity_types == ["cat", "dog", "elephant"]
        assert parameters.entity_extraction.llm["api_base"] == "http://some/base"
        assert parameters.entity_extraction.max_gleanings == 112
        assert parameters.entity_extraction.prompt == "Hello, World! C"
        assert parameters.input.base_dir == "/some/input/dir"
        assert parameters.input.connection_string == "input_cs"
        assert parameters.input.container_name == "input_cn"
        assert parameters.input.document_attribute_columns == ["test1", "test2"]
        assert parameters.input.file_encoding == "utf-16"
        assert parameters.input.file_pattern == ".*\\test\\.txt$"
        assert parameters.input.source_column == "test_source"
        assert parameters.input.storage_type == "blob"
        assert parameters.input.text_column == "test_text"
        assert parameters.input.timestamp_column == "test_timestamp"
        assert parameters.input.timestamp_format == "test_format"
        assert parameters.input.title_column == "test_title"
        assert parameters.input.type == PipelineInputType.text
        assert parameters.llm["api_base"] == "http://some/base"
        assert parameters.llm["api_key"] == "test"
        assert parameters.llm["api_version"] == "v1234"
        assert parameters.llm["concurrent_requests"] == 12
        assert parameters.llm["deployment_name"] == "model-deployment-name-x"
        assert parameters.llm["max_retries"] == 312
        assert parameters.llm["max_retry_wait"] == 0.1122
        assert parameters.llm["max_tokens"] == 15000
        assert parameters.llm["model"] == "test-llm"
        assert parameters.llm["model_supports_json"]
        assert parameters.llm["organization"] == "test_org"
        assert parameters.llm["proxy"] == "http://some/proxy"
        assert parameters.llm["request_timeout"] == 12.7
        assert parameters.llm["requests_per_minute"] == 900
        assert parameters.llm["sleep_on_rate_limit_recommendation"] is False
        assert parameters.llm["tokens_per_minute"] == 8000
        assert parameters.llm["type"] == "azure_openai_chat"
        assert parameters.parallelization["num_threads"] == 987
        assert parameters.parallelization["stagger"] == 0.123
        assert parameters.reporting.base_dir == "/some/reporting/dir"
        assert parameters.reporting.connection_string == "test_cs2"
        assert parameters.reporting.container_name == "test_cn2"
        assert parameters.reporting.type == PipelineReportingType.blob
        assert parameters.skip_workflows == ["a", "b", "c"]
        assert parameters.snapshots.graphml
        assert parameters.snapshots.raw_entities
        assert parameters.snapshots.top_level_nodes
        assert parameters.storage.base_dir == "/some/storage/dir"
        assert parameters.storage.connection_string == "test_cs"
        assert parameters.storage.container_name == "test_cn"
        assert parameters.storage.type == PipelineStorageType.blob
        assert parameters.summarize_descriptions.max_length == 12345
        assert parameters.summarize_descriptions.prompt == "Hello, World! D"
        assert parameters.umap.enabled

    @mock.patch.dict(os.environ, {"API_KEY_X": "test"}, clear=True)
    def test_create_parameters(self) -> None:
        parameters = default_config_parameters(
            DefaultConfigParametersModel(
                llm=LLMParametersModel(api_key="${API_KEY_X}", model="test-llm"),
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
                claim_extraction=ClaimExtractionConfigModel(description="test 123"),
                cluster_graph=ClusterGraphConfigModel(
                    max_cluster_size=123,
                ),
                umap=UmapConfigModel(enabled=True),
                encoding_model="test123",
                skip_workflows=["a", "b", "c"],
            ),
            ".",
        )
        assert parameters.llm["api_key"] == "test"
        assert parameters.llm["model"] == "test-llm"
        assert parameters.encoding_model == "test123"
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
        assert parameters.claim_extraction.description == "test 123"
        assert parameters.cluster_graph.max_cluster_size == 123
        assert parameters.umap.enabled


@mock.patch.dict(
    os.environ,
    {
        "PIPELINE_LLM_API_KEY": "test",
        "PIPELINE_LLM_API_BASE": "http://test",
        "PIPELINE_LLM_API_VERSION": "v1",
        "PIPELINE_LLM_MODEL": "test-llm",
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
    parameters = default_config_parameters(model, ".")

    assert parameters.llm["api_key"] == "test"
    assert parameters.llm["model"] == "test-llm"
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
