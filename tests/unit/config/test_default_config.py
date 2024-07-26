# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import json
import os
import re
import unittest
from pathlib import Path
from typing import Any, cast
from unittest import mock

import pytest
import yaml
from pydantic import ValidationError

import graphrag.config.defaults as defs
from graphrag.config import (
    ApiKeyMissingError,
    AzureApiBaseMissingError,
    AzureDeploymentNameMissingError,
    CacheConfig,
    CacheConfigInput,
    CacheType,
    ChunkingConfig,
    ChunkingConfigInput,
    ClaimExtractionConfig,
    ClaimExtractionConfigInput,
    ClusterGraphConfig,
    ClusterGraphConfigInput,
    CommunityReportsConfig,
    CommunityReportsConfigInput,
    EmbedGraphConfig,
    EmbedGraphConfigInput,
    EntityExtractionConfig,
    EntityExtractionConfigInput,
    GlobalSearchConfig,
    GraphRagConfig,
    GraphRagConfigInput,
    InputConfig,
    InputConfigInput,
    InputFileType,
    InputType,
    LLMParameters,
    LLMParametersInput,
    LocalSearchConfig,
    ParallelizationParameters,
    ReportingConfig,
    ReportingConfigInput,
    ReportingType,
    SnapshotsConfig,
    SnapshotsConfigInput,
    StorageConfig,
    StorageConfigInput,
    StorageType,
    SummarizeDescriptionsConfig,
    SummarizeDescriptionsConfigInput,
    TextEmbeddingConfig,
    TextEmbeddingConfigInput,
    UmapConfig,
    UmapConfigInput,
    create_graphrag_config,
)
from graphrag.index import (
    PipelineConfig,
    PipelineCSVInputConfig,
    PipelineFileCacheConfig,
    PipelineFileReportingConfig,
    PipelineFileStorageConfig,
    PipelineInputConfig,
    PipelineTextInputConfig,
    PipelineWorkflowReference,
    create_pipeline_config,
)

current_dir = os.path.dirname(__file__)

ALL_ENV_VARS = {
    "GRAPHRAG_API_BASE": "http://some/base",
    "GRAPHRAG_API_KEY": "test",
    "GRAPHRAG_API_ORGANIZATION": "test_org",
    "GRAPHRAG_API_PROXY": "http://some/proxy",
    "GRAPHRAG_API_VERSION": "v1234",
    "GRAPHRAG_ASYNC_MODE": "asyncio",
    "GRAPHRAG_CACHE_STORAGE_ACCOUNT_BLOB_URL": "cache_account_blob_url",
    "GRAPHRAG_CACHE_BASE_DIR": "/some/cache/dir",
    "GRAPHRAG_CACHE_CONNECTION_STRING": "test_cs1",
    "GRAPHRAG_CACHE_CONTAINER_NAME": "test_cn1",
    "GRAPHRAG_CACHE_TYPE": "blob",
    "GRAPHRAG_CHUNK_BY_COLUMNS": "a,b",
    "GRAPHRAG_CHUNK_OVERLAP": "12",
    "GRAPHRAG_CHUNK_SIZE": "500",
    "GRAPHRAG_CHUNK_ENCODING_MODEL": "encoding-c",
    "GRAPHRAG_CLAIM_EXTRACTION_ENABLED": "True",
    "GRAPHRAG_CLAIM_EXTRACTION_DESCRIPTION": "test 123",
    "GRAPHRAG_CLAIM_EXTRACTION_MAX_GLEANINGS": "5000",
    "GRAPHRAG_CLAIM_EXTRACTION_PROMPT_FILE": "tests/unit/config/prompt-a.txt",
    "GRAPHRAG_CLAIM_EXTRACTION_ENCODING_MODEL": "encoding_a",
    "GRAPHRAG_COMMUNITY_REPORTS_MAX_LENGTH": "23456",
    "GRAPHRAG_COMMUNITY_REPORTS_PROMPT_FILE": "tests/unit/config/prompt-b.txt",
    "GRAPHRAG_EMBEDDING_BATCH_MAX_TOKENS": "17",
    "GRAPHRAG_EMBEDDING_BATCH_SIZE": "1000000",
    "GRAPHRAG_EMBEDDING_CONCURRENT_REQUESTS": "12",
    "GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME": "model-deployment-name",
    "GRAPHRAG_EMBEDDING_MAX_RETRIES": "3",
    "GRAPHRAG_EMBEDDING_MAX_RETRY_WAIT": "0.1123",
    "GRAPHRAG_EMBEDDING_MODEL": "text-embedding-2",
    "GRAPHRAG_EMBEDDING_REQUESTS_PER_MINUTE": "500",
    "GRAPHRAG_EMBEDDING_SKIP": "a1,b1,c1",
    "GRAPHRAG_EMBEDDING_SLEEP_ON_RATE_LIMIT_RECOMMENDATION": "False",
    "GRAPHRAG_EMBEDDING_TARGET": "all",
    "GRAPHRAG_EMBEDDING_THREAD_COUNT": "2345",
    "GRAPHRAG_EMBEDDING_THREAD_STAGGER": "0.456",
    "GRAPHRAG_EMBEDDING_TOKENS_PER_MINUTE": "7000",
    "GRAPHRAG_EMBEDDING_TYPE": "azure_openai_embedding",
    "GRAPHRAG_ENCODING_MODEL": "test123",
    "GRAPHRAG_INPUT_STORAGE_ACCOUNT_BLOB_URL": "input_account_blob_url",
    "GRAPHRAG_ENTITY_EXTRACTION_ENTITY_TYPES": "cat,dog,elephant",
    "GRAPHRAG_ENTITY_EXTRACTION_MAX_GLEANINGS": "112",
    "GRAPHRAG_ENTITY_EXTRACTION_PROMPT_FILE": "tests/unit/config/prompt-c.txt",
    "GRAPHRAG_ENTITY_EXTRACTION_ENCODING_MODEL": "encoding_b",
    "GRAPHRAG_INPUT_BASE_DIR": "/some/input/dir",
    "GRAPHRAG_INPUT_CONNECTION_STRING": "input_cs",
    "GRAPHRAG_INPUT_CONTAINER_NAME": "input_cn",
    "GRAPHRAG_INPUT_DOCUMENT_ATTRIBUTE_COLUMNS": "test1,test2",
    "GRAPHRAG_INPUT_ENCODING": "utf-16",
    "GRAPHRAG_INPUT_FILE_PATTERN": ".*\\test\\.txt$",
    "GRAPHRAG_INPUT_SOURCE_COLUMN": "test_source",
    "GRAPHRAG_INPUT_TYPE": "blob",
    "GRAPHRAG_INPUT_TEXT_COLUMN": "test_text",
    "GRAPHRAG_INPUT_TIMESTAMP_COLUMN": "test_timestamp",
    "GRAPHRAG_INPUT_TIMESTAMP_FORMAT": "test_format",
    "GRAPHRAG_INPUT_TITLE_COLUMN": "test_title",
    "GRAPHRAG_INPUT_FILE_TYPE": "text",
    "GRAPHRAG_LLM_CONCURRENT_REQUESTS": "12",
    "GRAPHRAG_LLM_DEPLOYMENT_NAME": "model-deployment-name-x",
    "GRAPHRAG_LLM_MAX_RETRIES": "312",
    "GRAPHRAG_LLM_MAX_RETRY_WAIT": "0.1122",
    "GRAPHRAG_LLM_MAX_TOKENS": "15000",
    "GRAPHRAG_LLM_MODEL_SUPPORTS_JSON": "true",
    "GRAPHRAG_LLM_MODEL": "test-llm",
    "GRAPHRAG_LLM_N": "1",
    "GRAPHRAG_LLM_REQUEST_TIMEOUT": "12.7",
    "GRAPHRAG_LLM_REQUESTS_PER_MINUTE": "900",
    "GRAPHRAG_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION": "False",
    "GRAPHRAG_LLM_THREAD_COUNT": "987",
    "GRAPHRAG_LLM_THREAD_STAGGER": "0.123",
    "GRAPHRAG_LLM_TOKENS_PER_MINUTE": "8000",
    "GRAPHRAG_LLM_TYPE": "azure_openai_chat",
    "GRAPHRAG_MAX_CLUSTER_SIZE": "123",
    "GRAPHRAG_NODE2VEC_ENABLED": "true",
    "GRAPHRAG_NODE2VEC_ITERATIONS": "878787",
    "GRAPHRAG_NODE2VEC_NUM_WALKS": "5000000",
    "GRAPHRAG_NODE2VEC_RANDOM_SEED": "010101",
    "GRAPHRAG_NODE2VEC_WALK_LENGTH": "555111",
    "GRAPHRAG_NODE2VEC_WINDOW_SIZE": "12345",
    "GRAPHRAG_REPORTING_STORAGE_ACCOUNT_BLOB_URL": "reporting_account_blob_url",
    "GRAPHRAG_REPORTING_BASE_DIR": "/some/reporting/dir",
    "GRAPHRAG_REPORTING_CONNECTION_STRING": "test_cs2",
    "GRAPHRAG_REPORTING_CONTAINER_NAME": "test_cn2",
    "GRAPHRAG_REPORTING_TYPE": "blob",
    "GRAPHRAG_SKIP_WORKFLOWS": "a,b,c",
    "GRAPHRAG_SNAPSHOT_GRAPHML": "true",
    "GRAPHRAG_SNAPSHOT_RAW_ENTITIES": "true",
    "GRAPHRAG_SNAPSHOT_TOP_LEVEL_NODES": "true",
    "GRAPHRAG_STORAGE_STORAGE_ACCOUNT_BLOB_URL": "storage_account_blob_url",
    "GRAPHRAG_STORAGE_BASE_DIR": "/some/storage/dir",
    "GRAPHRAG_STORAGE_CONNECTION_STRING": "test_cs",
    "GRAPHRAG_STORAGE_CONTAINER_NAME": "test_cn",
    "GRAPHRAG_STORAGE_TYPE": "blob",
    "GRAPHRAG_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH": "12345",
    "GRAPHRAG_SUMMARIZE_DESCRIPTIONS_PROMPT_FILE": "tests/unit/config/prompt-d.txt",
    "GRAPHRAG_LLM_TEMPERATURE": "0.0",
    "GRAPHRAG_LLM_TOP_P": "1.0",
    "GRAPHRAG_UMAP_ENABLED": "true",
    "GRAPHRAG_LOCAL_SEARCH_TEXT_UNIT_PROP": "0.713",
    "GRAPHRAG_LOCAL_SEARCH_COMMUNITY_PROP": "0.1234",
    "GRAPHRAG_LOCAL_SEARCH_LLM_TEMPERATURE": "0.1",
    "GRAPHRAG_LOCAL_SEARCH_LLM_TOP_P": "0.9",
    "GRAPHRAG_LOCAL_SEARCH_LLM_N": "2",
    "GRAPHRAG_LOCAL_SEARCH_LLM_MAX_TOKENS": "12",
    "GRAPHRAG_LOCAL_SEARCH_TOP_K_RELATIONSHIPS": "15",
    "GRAPHRAG_LOCAL_SEARCH_TOP_K_ENTITIES": "14",
    "GRAPHRAG_LOCAL_SEARCH_CONVERSATION_HISTORY_MAX_TURNS": "2",
    "GRAPHRAG_LOCAL_SEARCH_MAX_TOKENS": "142435",
    "GRAPHRAG_GLOBAL_SEARCH_LLM_TEMPERATURE": "0.1",
    "GRAPHRAG_GLOBAL_SEARCH_LLM_TOP_P": "0.9",
    "GRAPHRAG_GLOBAL_SEARCH_LLM_N": "2",
    "GRAPHRAG_GLOBAL_SEARCH_MAX_TOKENS": "5123",
    "GRAPHRAG_GLOBAL_SEARCH_DATA_MAX_TOKENS": "123",
    "GRAPHRAG_GLOBAL_SEARCH_MAP_MAX_TOKENS": "4123",
    "GRAPHRAG_GLOBAL_SEARCH_CONCURRENCY": "7",
    "GRAPHRAG_GLOBAL_SEARCH_REDUCE_MAX_TOKENS": "15432",
}


class TestDefaultConfig(unittest.TestCase):
    def test_clear_warnings(self):
        """Just clearing unused import warnings"""
        assert CacheConfig is not None
        assert ChunkingConfig is not None
        assert ClaimExtractionConfig is not None
        assert ClusterGraphConfig is not None
        assert CommunityReportsConfig is not None
        assert EmbedGraphConfig is not None
        assert EntityExtractionConfig is not None
        assert GlobalSearchConfig is not None
        assert GraphRagConfig is not None
        assert InputConfig is not None
        assert LLMParameters is not None
        assert LocalSearchConfig is not None
        assert ParallelizationParameters is not None
        assert ReportingConfig is not None
        assert SnapshotsConfig is not None
        assert StorageConfig is not None
        assert SummarizeDescriptionsConfig is not None
        assert TextEmbeddingConfig is not None
        assert UmapConfig is not None
        assert PipelineConfig is not None
        assert PipelineFileReportingConfig is not None
        assert PipelineFileStorageConfig is not None
        assert PipelineInputConfig is not None
        assert PipelineFileCacheConfig is not None
        assert PipelineWorkflowReference is not None

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True)
    def test_string_repr(self):
        # __str__ can be json loaded
        config = create_graphrag_config()
        string_repr = str(config)
        assert string_repr is not None
        assert json.loads(string_repr) is not None

        # __repr__ can be eval()'d
        repr_str = config.__repr__()
        # TODO: add __repr__ to datashaper enum
        repr_str = repr_str.replace("async_mode=<AsyncType.Threaded: 'threaded'>,", "")
        assert eval(repr_str) is not None

        # Pipeline config __str__ can be json loaded
        pipeline_config = create_pipeline_config(config)
        string_repr = str(pipeline_config)
        assert string_repr is not None
        assert json.loads(string_repr) is not None

        # Pipeline config __repr__ can be eval()'d
        repr_str = pipeline_config.__repr__()
        # TODO: add __repr__ to datashaper enum
        repr_str = repr_str.replace(
            "'async_mode': <AsyncType.Threaded: 'threaded'>,", ""
        )
        assert eval(repr_str) is not None

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_default_config_with_no_env_vars_throws(self):
        with pytest.raises(ApiKeyMissingError):
            # This should throw an error because the API key is missing
            create_pipeline_config(create_graphrag_config())

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_default_config_with_api_key_passes(self):
        # doesn't throw
        config = create_pipeline_config(create_graphrag_config())
        assert config is not None

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True)
    def test_default_config_with_oai_key_passes_envvar(self):
        # doesn't throw
        config = create_pipeline_config(create_graphrag_config())
        assert config is not None

    def test_default_config_with_oai_key_passes_obj(self):
        # doesn't throw
        config = create_pipeline_config(
            create_graphrag_config({"llm": {"api_key": "test"}})
        )
        assert config is not None

    @mock.patch.dict(
        os.environ,
        {"GRAPHRAG_API_KEY": "test", "GRAPHRAG_LLM_TYPE": "azure_openai_chat"},
        clear=True,
    )
    def test_throws_if_azure_is_used_without_api_base_envvar(self):
        with pytest.raises(AzureApiBaseMissingError):
            create_graphrag_config()

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_throws_if_azure_is_used_without_api_base_obj(self):
        with pytest.raises(AzureApiBaseMissingError):
            create_graphrag_config(
                GraphRagConfigInput(llm=LLMParametersInput(type="azure_openai_chat"))
            )

    @mock.patch.dict(
        os.environ,
        {
            "GRAPHRAG_API_KEY": "test",
            "GRAPHRAG_LLM_TYPE": "azure_openai_chat",
            "GRAPHRAG_API_BASE": "http://some/base",
        },
        clear=True,
    )
    def test_throws_if_azure_is_used_without_llm_deployment_name_envvar(self):
        with pytest.raises(AzureDeploymentNameMissingError):
            create_graphrag_config()

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_throws_if_azure_is_used_without_llm_deployment_name_obj(self):
        with pytest.raises(AzureDeploymentNameMissingError):
            create_graphrag_config(
                GraphRagConfigInput(
                    llm=LLMParametersInput(
                        type="azure_openai_chat", api_base="http://some/base"
                    )
                )
            )

    @mock.patch.dict(
        os.environ,
        {
            "GRAPHRAG_API_KEY": "test",
            "GRAPHRAG_EMBEDDING_TYPE": "azure_openai_embedding",
            "GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME": "x",
        },
        clear=True,
    )
    def test_throws_if_azure_is_used_without_embedding_api_base_envvar(self):
        with pytest.raises(AzureApiBaseMissingError):
            create_graphrag_config()

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_throws_if_azure_is_used_without_embedding_api_base_obj(self):
        with pytest.raises(AzureApiBaseMissingError):
            create_graphrag_config(
                GraphRagConfigInput(
                    embeddings=TextEmbeddingConfigInput(
                        llm=LLMParametersInput(
                            type="azure_openai_embedding",
                            deployment_name="x",
                        )
                    ),
                )
            )

    @mock.patch.dict(
        os.environ,
        {
            "GRAPHRAG_API_KEY": "test",
            "GRAPHRAG_API_BASE": "http://some/base",
            "GRAPHRAG_LLM_DEPLOYMENT_NAME": "x",
            "GRAPHRAG_LLM_TYPE": "azure_openai_chat",
            "GRAPHRAG_EMBEDDING_TYPE": "azure_openai_embedding",
        },
        clear=True,
    )
    def test_throws_if_azure_is_used_without_embedding_deployment_name_envvar(self):
        with pytest.raises(AzureDeploymentNameMissingError):
            create_graphrag_config()

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_throws_if_azure_is_used_without_embedding_deployment_name_obj(self):
        with pytest.raises(AzureDeploymentNameMissingError):
            create_graphrag_config(
                GraphRagConfigInput(
                    llm=LLMParametersInput(
                        type="azure_openai_chat",
                        api_base="http://some/base",
                        deployment_name="model-deployment-name-x",
                    ),
                    embeddings=TextEmbeddingConfigInput(
                        llm=LLMParametersInput(
                            type="azure_openai_embedding",
                        )
                    ),
                )
            )

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_minimim_azure_config_object(self):
        config = create_graphrag_config(
            GraphRagConfigInput(
                llm=LLMParametersInput(
                    type="azure_openai_chat",
                    api_base="http://some/base",
                    deployment_name="model-deployment-name-x",
                ),
                embeddings=TextEmbeddingConfigInput(
                    llm=LLMParametersInput(
                        type="azure_openai_embedding",
                        deployment_name="model-deployment-name",
                    )
                ),
            )
        )
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
            create_graphrag_config()

    @mock.patch.dict(
        os.environ,
        {
            "GRAPHRAG_API_KEY": "test",
            "GRAPHRAG_LLM_TYPE": "azure_openai_chat",
            "GRAPHRAG_LLM_API_BASE": "http://some/base",
        },
        clear=True,
    )
    def test_throws_if_azure_is_used_without_llm_deployment_name(self):
        with pytest.raises(AzureDeploymentNameMissingError):
            create_graphrag_config()

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
            create_graphrag_config()

    @mock.patch.dict(
        os.environ,
        {"GRAPHRAG_API_KEY": "test", "GRAPHRAG_INPUT_FILE_TYPE": "csv"},
        clear=True,
    )
    def test_csv_input_returns_correct_config(self):
        config = create_pipeline_config(create_graphrag_config(root_dir="/some/root"))
        assert config.root_dir == "/some/root"
        # Make sure the input is a CSV input
        assert isinstance(config.input, PipelineCSVInputConfig)
        assert (config.input.file_pattern or "") == ".*\\.csv$"  # type: ignore

    @mock.patch.dict(
        os.environ,
        {"GRAPHRAG_API_KEY": "test", "GRAPHRAG_INPUT_FILE_TYPE": "text"},
        clear=True,
    )
    def test_text_input_returns_correct_config(self):
        config = create_pipeline_config(create_graphrag_config(root_dir="."))
        assert isinstance(config.input, PipelineTextInputConfig)
        assert config.input is not None
        assert (config.input.file_pattern or "") == ".*\\.txt$"  # type: ignore

    @mock.patch.dict(
        os.environ,
        {
            "GRAPHRAG_LLM_API_KEY": "test",
            "GRAPHRAG_ENTITY_EXTRACTION_MAX_GLEANINGS": "0",
            "GRAPHRAG_CLAIM_EXTRACTION_MAX_GLEANINGS": "0",
        },
        clear=True,
    )
    def test_can_set_gleanings_to_zero(self):
        parameters = create_graphrag_config()
        assert parameters.claim_extraction.max_gleanings == 0
        assert parameters.entity_extraction.max_gleanings == 0

    @mock.patch.dict(
        os.environ,
        {"GRAPHRAG_LLM_API_KEY": "test", "GRAPHRAG_CHUNK_BY_COLUMNS": ""},
        clear=True,
    )
    def test_can_set_no_chunk_by_columns(self):
        parameters = create_graphrag_config()
        assert parameters.chunks.group_by_columns == []

    def test_all_env_vars_is_accurate(self):
        env_var_docs_path = Path("docsite/posts/config/env_vars.md")
        query_docs_path = Path("docsite/posts/query/3-cli.md")

        env_var_docs = env_var_docs_path.read_text(encoding="utf-8")
        query_docs = query_docs_path.read_text(encoding="utf-8")

        def find_envvar_names(text) -> set[str]:
            pattern = r"`(GRAPHRAG_[^`]+)`"
            found = re.findall(pattern, text)
            found = {f for f in found if not f.endswith("_")}
            return {*found}

        graphrag_strings = find_envvar_names(env_var_docs) | find_envvar_names(
            query_docs
        )

        missing = {s for s in graphrag_strings if s not in ALL_ENV_VARS} - {
            # Remove configs covered by the base LLM connection configs
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
        {"GRAPHRAG_API_KEY": "test"},
        clear=True,
    )
    def test_malformed_input_dict_throws(self):
        with pytest.raises(ValidationError):
            create_graphrag_config(cast(Any, {"llm": 12}))

    @mock.patch.dict(
        os.environ,
        ALL_ENV_VARS,
        clear=True,
    )
    def test_create_parameters_from_env_vars(self) -> None:
        parameters = create_graphrag_config()
        assert parameters.async_mode == "asyncio"
        assert parameters.cache.storage_account_blob_url == "cache_account_blob_url"
        assert parameters.cache.base_dir == "/some/cache/dir"
        assert parameters.cache.connection_string == "test_cs1"
        assert parameters.cache.container_name == "test_cn1"
        assert parameters.cache.type == CacheType.blob
        assert parameters.chunks.group_by_columns == ["a", "b"]
        assert parameters.chunks.overlap == 12
        assert parameters.chunks.size == 500
        assert parameters.chunks.encoding_model == "encoding-c"
        assert parameters.claim_extraction.enabled
        assert parameters.claim_extraction.description == "test 123"
        assert parameters.claim_extraction.max_gleanings == 5000
        assert parameters.claim_extraction.prompt == "tests/unit/config/prompt-a.txt"
        assert parameters.claim_extraction.encoding_model == "encoding_a"
        assert parameters.cluster_graph.max_cluster_size == 123
        assert parameters.community_reports.max_length == 23456
        assert parameters.community_reports.prompt == "tests/unit/config/prompt-b.txt"
        assert parameters.embed_graph.enabled
        assert parameters.embed_graph.iterations == 878787
        assert parameters.embed_graph.num_walks == 5_000_000
        assert parameters.embed_graph.random_seed == 10101
        assert parameters.embed_graph.walk_length == 555111
        assert parameters.embed_graph.window_size == 12345
        assert parameters.embeddings.batch_max_tokens == 17
        assert parameters.embeddings.batch_size == 1_000_000
        assert parameters.embeddings.llm.concurrent_requests == 12
        assert parameters.embeddings.llm.deployment_name == "model-deployment-name"
        assert parameters.embeddings.llm.max_retries == 3
        assert parameters.embeddings.llm.max_retry_wait == 0.1123
        assert parameters.embeddings.llm.model == "text-embedding-2"
        assert parameters.embeddings.llm.requests_per_minute == 500
        assert parameters.embeddings.llm.sleep_on_rate_limit_recommendation is False
        assert parameters.embeddings.llm.tokens_per_minute == 7000
        assert parameters.embeddings.llm.type == "azure_openai_embedding"
        assert parameters.embeddings.parallelization.num_threads == 2345
        assert parameters.embeddings.parallelization.stagger == 0.456
        assert parameters.embeddings.skip == ["a1", "b1", "c1"]
        assert parameters.embeddings.target == "all"
        assert parameters.encoding_model == "test123"
        assert parameters.entity_extraction.entity_types == ["cat", "dog", "elephant"]
        assert parameters.entity_extraction.llm.api_base == "http://some/base"
        assert parameters.entity_extraction.max_gleanings == 112
        assert parameters.entity_extraction.prompt == "tests/unit/config/prompt-c.txt"
        assert parameters.entity_extraction.encoding_model == "encoding_b"
        assert parameters.input.storage_account_blob_url == "input_account_blob_url"
        assert parameters.input.base_dir == "/some/input/dir"
        assert parameters.input.connection_string == "input_cs"
        assert parameters.input.container_name == "input_cn"
        assert parameters.input.document_attribute_columns == ["test1", "test2"]
        assert parameters.input.encoding == "utf-16"
        assert parameters.input.file_pattern == ".*\\test\\.txt$"
        assert parameters.input.file_type == InputFileType.text
        assert parameters.input.source_column == "test_source"
        assert parameters.input.text_column == "test_text"
        assert parameters.input.timestamp_column == "test_timestamp"
        assert parameters.input.timestamp_format == "test_format"
        assert parameters.input.title_column == "test_title"
        assert parameters.input.type == InputType.blob
        assert parameters.llm.api_base == "http://some/base"
        assert parameters.llm.api_key == "test"
        assert parameters.llm.api_version == "v1234"
        assert parameters.llm.concurrent_requests == 12
        assert parameters.llm.deployment_name == "model-deployment-name-x"
        assert parameters.llm.max_retries == 312
        assert parameters.llm.max_retry_wait == 0.1122
        assert parameters.llm.max_tokens == 15000
        assert parameters.llm.model == "test-llm"
        assert parameters.llm.model_supports_json
        assert parameters.llm.n == 1
        assert parameters.llm.organization == "test_org"
        assert parameters.llm.proxy == "http://some/proxy"
        assert parameters.llm.request_timeout == 12.7
        assert parameters.llm.requests_per_minute == 900
        assert parameters.llm.sleep_on_rate_limit_recommendation is False
        assert parameters.llm.temperature == 0.0
        assert parameters.llm.top_p == 1.0
        assert parameters.llm.tokens_per_minute == 8000
        assert parameters.llm.type == "azure_openai_chat"
        assert parameters.parallelization.num_threads == 987
        assert parameters.parallelization.stagger == 0.123
        assert (
            parameters.reporting.storage_account_blob_url
            == "reporting_account_blob_url"
        )
        assert parameters.reporting.base_dir == "/some/reporting/dir"
        assert parameters.reporting.connection_string == "test_cs2"
        assert parameters.reporting.container_name == "test_cn2"
        assert parameters.reporting.type == ReportingType.blob
        assert parameters.skip_workflows == ["a", "b", "c"]
        assert parameters.snapshots.graphml
        assert parameters.snapshots.raw_entities
        assert parameters.snapshots.top_level_nodes
        assert parameters.storage.storage_account_blob_url == "storage_account_blob_url"
        assert parameters.storage.base_dir == "/some/storage/dir"
        assert parameters.storage.connection_string == "test_cs"
        assert parameters.storage.container_name == "test_cn"
        assert parameters.storage.type == StorageType.blob
        assert parameters.summarize_descriptions.max_length == 12345
        assert (
            parameters.summarize_descriptions.prompt == "tests/unit/config/prompt-d.txt"
        )
        assert parameters.umap.enabled
        assert parameters.local_search.text_unit_prop == 0.713
        assert parameters.local_search.community_prop == 0.1234
        assert parameters.local_search.llm_max_tokens == 12
        assert parameters.local_search.top_k_relationships == 15
        assert parameters.local_search.conversation_history_max_turns == 2
        assert parameters.local_search.top_k_entities == 14
        assert parameters.local_search.temperature == 0.1
        assert parameters.local_search.top_p == 0.9
        assert parameters.local_search.n == 2
        assert parameters.local_search.max_tokens == 142435

        assert parameters.global_search.temperature == 0.1
        assert parameters.global_search.top_p == 0.9
        assert parameters.global_search.n == 2
        assert parameters.global_search.max_tokens == 5123
        assert parameters.global_search.data_max_tokens == 123
        assert parameters.global_search.map_max_tokens == 4123
        assert parameters.global_search.concurrency == 7
        assert parameters.global_search.reduce_max_tokens == 15432

    @mock.patch.dict(os.environ, {"API_KEY_X": "test"}, clear=True)
    def test_create_parameters(self) -> None:
        parameters = create_graphrag_config(
            GraphRagConfigInput(
                llm=LLMParametersInput(api_key="${API_KEY_X}", model="test-llm"),
                storage=StorageConfigInput(
                    type=StorageType.blob,
                    connection_string="test_cs",
                    container_name="test_cn",
                    base_dir="/some/storage/dir",
                    storage_account_blob_url="storage_account_blob_url",
                ),
                cache=CacheConfigInput(
                    type=CacheType.blob,
                    connection_string="test_cs1",
                    container_name="test_cn1",
                    base_dir="/some/cache/dir",
                    storage_account_blob_url="cache_account_blob_url",
                ),
                reporting=ReportingConfigInput(
                    type=ReportingType.blob,
                    connection_string="test_cs2",
                    container_name="test_cn2",
                    base_dir="/some/reporting/dir",
                    storage_account_blob_url="reporting_account_blob_url",
                ),
                input=InputConfigInput(
                    file_type=InputFileType.text,
                    file_encoding="utf-16",
                    document_attribute_columns=["test1", "test2"],
                    base_dir="/some/input/dir",
                    connection_string="input_cs",
                    container_name="input_cn",
                    file_pattern=".*\\test\\.txt$",
                    source_column="test_source",
                    text_column="test_text",
                    timestamp_column="test_timestamp",
                    timestamp_format="test_format",
                    title_column="test_title",
                    type="blob",
                    storage_account_blob_url="input_account_blob_url",
                ),
                embed_graph=EmbedGraphConfigInput(
                    enabled=True,
                    num_walks=5_000_000,
                    iterations=878787,
                    random_seed=10101,
                    walk_length=555111,
                ),
                embeddings=TextEmbeddingConfigInput(
                    batch_size=1_000_000,
                    batch_max_tokens=8000,
                    skip=["a1", "b1", "c1"],
                    llm=LLMParametersInput(model="text-embedding-2"),
                ),
                chunks=ChunkingConfigInput(
                    size=500, overlap=12, group_by_columns=["a", "b"]
                ),
                snapshots=SnapshotsConfigInput(
                    graphml=True,
                    raw_entities=True,
                    top_level_nodes=True,
                ),
                entity_extraction=EntityExtractionConfigInput(
                    max_gleanings=112,
                    entity_types=["cat", "dog", "elephant"],
                    prompt="entity_extraction_prompt_file.txt",
                ),
                summarize_descriptions=SummarizeDescriptionsConfigInput(
                    max_length=12345, prompt="summarize_prompt_file.txt"
                ),
                community_reports=CommunityReportsConfigInput(
                    max_length=23456,
                    prompt="community_report_prompt_file.txt",
                    max_input_length=12345,
                ),
                claim_extraction=ClaimExtractionConfigInput(
                    description="test 123",
                    max_gleanings=5000,
                    prompt="claim_extraction_prompt_file.txt",
                ),
                cluster_graph=ClusterGraphConfigInput(
                    max_cluster_size=123,
                ),
                umap=UmapConfigInput(enabled=True),
                encoding_model="test123",
                skip_workflows=["a", "b", "c"],
            ),
            ".",
        )

        assert parameters.cache.base_dir == "/some/cache/dir"
        assert parameters.cache.connection_string == "test_cs1"
        assert parameters.cache.container_name == "test_cn1"
        assert parameters.cache.type == CacheType.blob
        assert parameters.cache.storage_account_blob_url == "cache_account_blob_url"
        assert parameters.chunks.group_by_columns == ["a", "b"]
        assert parameters.chunks.overlap == 12
        assert parameters.chunks.size == 500
        assert parameters.claim_extraction.description == "test 123"
        assert parameters.claim_extraction.max_gleanings == 5000
        assert parameters.claim_extraction.prompt == "claim_extraction_prompt_file.txt"
        assert parameters.cluster_graph.max_cluster_size == 123
        assert parameters.community_reports.max_input_length == 12345
        assert parameters.community_reports.max_length == 23456
        assert parameters.community_reports.prompt == "community_report_prompt_file.txt"
        assert parameters.embed_graph.enabled
        assert parameters.embed_graph.iterations == 878787
        assert parameters.embed_graph.num_walks == 5_000_000
        assert parameters.embed_graph.random_seed == 10101
        assert parameters.embed_graph.walk_length == 555111
        assert parameters.embeddings.batch_max_tokens == 8000
        assert parameters.embeddings.batch_size == 1_000_000
        assert parameters.embeddings.llm.model == "text-embedding-2"
        assert parameters.embeddings.skip == ["a1", "b1", "c1"]
        assert parameters.encoding_model == "test123"
        assert parameters.entity_extraction.entity_types == ["cat", "dog", "elephant"]
        assert parameters.entity_extraction.max_gleanings == 112
        assert (
            parameters.entity_extraction.prompt == "entity_extraction_prompt_file.txt"
        )
        assert parameters.input.base_dir == "/some/input/dir"
        assert parameters.input.connection_string == "input_cs"
        assert parameters.input.container_name == "input_cn"
        assert parameters.input.document_attribute_columns == ["test1", "test2"]
        assert parameters.input.encoding == "utf-16"
        assert parameters.input.file_pattern == ".*\\test\\.txt$"
        assert parameters.input.source_column == "test_source"
        assert parameters.input.type == "blob"
        assert parameters.input.text_column == "test_text"
        assert parameters.input.timestamp_column == "test_timestamp"
        assert parameters.input.timestamp_format == "test_format"
        assert parameters.input.title_column == "test_title"
        assert parameters.input.file_type == InputFileType.text
        assert parameters.input.storage_account_blob_url == "input_account_blob_url"
        assert parameters.llm.api_key == "test"
        assert parameters.llm.model == "test-llm"
        assert parameters.reporting.base_dir == "/some/reporting/dir"
        assert parameters.reporting.connection_string == "test_cs2"
        assert parameters.reporting.container_name == "test_cn2"
        assert parameters.reporting.type == ReportingType.blob
        assert (
            parameters.reporting.storage_account_blob_url
            == "reporting_account_blob_url"
        )
        assert parameters.skip_workflows == ["a", "b", "c"]
        assert parameters.snapshots.graphml
        assert parameters.snapshots.raw_entities
        assert parameters.snapshots.top_level_nodes
        assert parameters.storage.base_dir == "/some/storage/dir"
        assert parameters.storage.connection_string == "test_cs"
        assert parameters.storage.container_name == "test_cn"
        assert parameters.storage.type == StorageType.blob
        assert parameters.storage.storage_account_blob_url == "storage_account_blob_url"
        assert parameters.summarize_descriptions.max_length == 12345
        assert parameters.summarize_descriptions.prompt == "summarize_prompt_file.txt"
        assert parameters.umap.enabled

    @mock.patch.dict(
        os.environ,
        {"GRAPHRAG_API_KEY": "test"},
        clear=True,
    )
    def test_default_values(self) -> None:
        parameters = create_graphrag_config()
        assert parameters.async_mode == defs.ASYNC_MODE
        assert parameters.cache.base_dir == defs.CACHE_BASE_DIR
        assert parameters.cache.type == defs.CACHE_TYPE
        assert parameters.cache.base_dir == defs.CACHE_BASE_DIR
        assert parameters.chunks.group_by_columns == defs.CHUNK_GROUP_BY_COLUMNS
        assert parameters.chunks.overlap == defs.CHUNK_OVERLAP
        assert parameters.chunks.size == defs.CHUNK_SIZE
        assert parameters.claim_extraction.description == defs.CLAIM_DESCRIPTION
        assert parameters.claim_extraction.max_gleanings == defs.CLAIM_MAX_GLEANINGS
        assert (
            parameters.community_reports.max_input_length
            == defs.COMMUNITY_REPORT_MAX_INPUT_LENGTH
        )
        assert (
            parameters.community_reports.max_length == defs.COMMUNITY_REPORT_MAX_LENGTH
        )
        assert parameters.embeddings.batch_max_tokens == defs.EMBEDDING_BATCH_MAX_TOKENS
        assert parameters.embeddings.batch_size == defs.EMBEDDING_BATCH_SIZE
        assert parameters.embeddings.llm.model == defs.EMBEDDING_MODEL
        assert parameters.embeddings.target == defs.EMBEDDING_TARGET
        assert parameters.embeddings.llm.type == defs.EMBEDDING_TYPE
        assert (
            parameters.embeddings.llm.requests_per_minute
            == defs.LLM_REQUESTS_PER_MINUTE
        )
        assert parameters.embeddings.llm.tokens_per_minute == defs.LLM_TOKENS_PER_MINUTE
        assert (
            parameters.embeddings.llm.sleep_on_rate_limit_recommendation
            == defs.LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION
        )
        assert (
            parameters.entity_extraction.entity_types
            == defs.ENTITY_EXTRACTION_ENTITY_TYPES
        )
        assert (
            parameters.entity_extraction.max_gleanings
            == defs.ENTITY_EXTRACTION_MAX_GLEANINGS
        )
        assert parameters.encoding_model == defs.ENCODING_MODEL
        assert parameters.input.base_dir == defs.INPUT_BASE_DIR
        assert parameters.input.file_pattern == defs.INPUT_CSV_PATTERN
        assert parameters.input.encoding == defs.INPUT_FILE_ENCODING
        assert parameters.input.type == defs.INPUT_TYPE
        assert parameters.input.base_dir == defs.INPUT_BASE_DIR
        assert parameters.input.text_column == defs.INPUT_TEXT_COLUMN
        assert parameters.input.file_type == defs.INPUT_FILE_TYPE
        assert parameters.llm.concurrent_requests == defs.LLM_CONCURRENT_REQUESTS
        assert parameters.llm.max_retries == defs.LLM_MAX_RETRIES
        assert parameters.llm.max_retry_wait == defs.LLM_MAX_RETRY_WAIT
        assert parameters.llm.max_tokens == defs.LLM_MAX_TOKENS
        assert parameters.llm.model == defs.LLM_MODEL
        assert parameters.llm.request_timeout == defs.LLM_REQUEST_TIMEOUT
        assert parameters.llm.requests_per_minute == defs.LLM_REQUESTS_PER_MINUTE
        assert parameters.llm.tokens_per_minute == defs.LLM_TOKENS_PER_MINUTE
        assert (
            parameters.llm.sleep_on_rate_limit_recommendation
            == defs.LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION
        )
        assert parameters.llm.type == defs.LLM_TYPE
        assert parameters.cluster_graph.max_cluster_size == defs.MAX_CLUSTER_SIZE
        assert parameters.embed_graph.enabled == defs.NODE2VEC_ENABLED
        assert parameters.embed_graph.iterations == defs.NODE2VEC_ITERATIONS
        assert parameters.embed_graph.num_walks == defs.NODE2VEC_NUM_WALKS
        assert parameters.embed_graph.random_seed == defs.NODE2VEC_RANDOM_SEED
        assert parameters.embed_graph.walk_length == defs.NODE2VEC_WALK_LENGTH
        assert parameters.embed_graph.window_size == defs.NODE2VEC_WINDOW_SIZE
        assert (
            parameters.parallelization.num_threads == defs.PARALLELIZATION_NUM_THREADS
        )
        assert parameters.parallelization.stagger == defs.PARALLELIZATION_STAGGER
        assert parameters.reporting.type == defs.REPORTING_TYPE
        assert parameters.reporting.base_dir == defs.REPORTING_BASE_DIR
        assert parameters.snapshots.graphml == defs.SNAPSHOTS_GRAPHML
        assert parameters.snapshots.raw_entities == defs.SNAPSHOTS_RAW_ENTITIES
        assert parameters.snapshots.top_level_nodes == defs.SNAPSHOTS_TOP_LEVEL_NODES
        assert parameters.storage.base_dir == defs.STORAGE_BASE_DIR
        assert parameters.storage.type == defs.STORAGE_TYPE
        assert parameters.umap.enabled == defs.UMAP_ENABLED

    @mock.patch.dict(
        os.environ,
        {"GRAPHRAG_API_KEY": "test"},
        clear=True,
    )
    def test_prompt_file_reading(self):
        config = create_graphrag_config({
            "entity_extraction": {"prompt": "tests/unit/config/prompt-a.txt"},
            "claim_extraction": {"prompt": "tests/unit/config/prompt-b.txt"},
            "community_reports": {"prompt": "tests/unit/config/prompt-c.txt"},
            "summarize_descriptions": {"prompt": "tests/unit/config/prompt-d.txt"},
        })
        strategy = config.entity_extraction.resolved_strategy(".", "abc123")
        assert strategy["extraction_prompt"] == "Hello, World! A"
        assert strategy["encoding_name"] == "abc123"

        strategy = config.claim_extraction.resolved_strategy(".", "encoding_b")
        assert strategy["extraction_prompt"] == "Hello, World! B"

        strategy = config.community_reports.resolved_strategy(".")
        assert strategy["extraction_prompt"] == "Hello, World! C"

        strategy = config.summarize_descriptions.resolved_strategy(".")
        assert strategy["summarize_prompt"] == "Hello, World! D"


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
  file_type: text

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
    model = config_dict
    parameters = create_graphrag_config(model, ".")

    assert parameters.llm.api_key == "test"
    assert parameters.llm.model == "test-llm"
    assert parameters.llm.api_base == "http://test"
    assert parameters.llm.api_version == "v1"
    assert parameters.llm.deployment_name == "test"

    # generate the pipeline from the default parameters
    pipeline_config = create_pipeline_config(parameters, True)

    config_str = pipeline_config.model_dump_json()
    assert "${PIPELINE_LLM_API_KEY}" not in config_str
    assert "${PIPELINE_LLM_API_BASE}" not in config_str
    assert "${PIPELINE_LLM_API_VERSION}" not in config_str
    assert "${PIPELINE_LLM_MODEL}" not in config_str
    assert "${PIPELINE_LLM_DEPLOYMENT_NAME}" not in config_str
