# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

import os
from enum import Enum
from pathlib import Path
from typing import cast

from datashaper import AsyncType
from environs import Env
from pydantic import TypeAdapter

from graphrag.index.config import (
    PipelineCacheType,
    PipelineInputStorageType,
    PipelineInputType,
    PipelineReportingType,
    PipelineStorageType,
)
from graphrag.index.default_config.parameters.models import TextEmbeddingTarget
from graphrag.index.default_config.parameters.read_dotenv import read_dotenv
from graphrag.index.llm.types import LLMType

from .defaults import (
    DEFAULT_ASYNC_MODE,
    DEFAULT_CACHE_BASE_DIR,
    DEFAULT_CACHE_TYPE,
    DEFAULT_CHUNK_GROUP_BY_COLUMNS,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CLAIM_DESCRIPTION,
    DEFAULT_CLAIM_MAX_GLEANINGS,
    DEFAULT_COMMUNITY_REPORT_MAX_INPUT_LENGTH,
    DEFAULT_COMMUNITY_REPORT_MAX_LENGTH,
    DEFAULT_EMBEDDING_BATCH_MAX_TOKENS,
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_TARGET,
    DEFAULT_EMBEDDING_TYPE,
    DEFAULT_ENCODING_MODEL,
    DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
    DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS,
    DEFAULT_INPUT_BASE_DIR,
    DEFAULT_INPUT_CSV_PATTERN,
    DEFAULT_INPUT_FILE_ENCODING,
    DEFAULT_INPUT_STORAGE_TYPE,
    DEFAULT_INPUT_TEXT_COLUMN,
    DEFAULT_INPUT_TEXT_PATTERN,
    DEFAULT_INPUT_TYPE,
    DEFAULT_LLM_CONCURRENT_REQUESTS,
    DEFAULT_LLM_MAX_RETRIES,
    DEFAULT_LLM_MAX_RETRY_WAIT,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_REQUEST_TIMEOUT,
    DEFAULT_LLM_REQUESTS_PER_MINUTE,
    DEFAULT_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION,
    DEFAULT_LLM_TOKENS_PER_MINUTE,
    DEFAULT_LLM_TYPE,
    DEFAULT_MAX_CLUSTER_SIZE,
    DEFAULT_NODE2VEC_IS_ENABLED,
    DEFAULT_NODE2VEC_ITERATIONS,
    DEFAULT_NODE2VEC_NUM_WALKS,
    DEFAULT_NODE2VEC_RANDOM_SEED,
    DEFAULT_NODE2VEC_WALK_LENGTH,
    DEFAULT_NODE2VEC_WINDOW_SIZE,
    DEFAULT_PARALLELIZATION_NUM_THREADS,
    DEFAULT_PARALLELIZATION_STAGGER,
    DEFAULT_REPORTING_BASE_DIR,
    DEFAULT_REPORTING_TYPE,
    DEFAULT_SNAPSHOTS_GRAPHML,
    DEFAULT_SNAPSHOTS_RAW_ENTITIES,
    DEFAULT_SNAPSHOTS_TOP_LEVEL_NODES,
    DEFAULT_STORAGE_BASE_DIR,
    DEFAULT_STORAGE_TYPE,
    DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
    DEFAULT_UMAP_ENABLED,
)
from .environment_reader import EnvironmentReader
from .errors import (
    ApiKeyMissingError,
    AzureApiBaseMissingError,
    AzureDeploymentNameMissingError,
)
from .input_models import (
    DefaultConfigParametersInputModel,
    LLMConfigInputModel,
)
from .models import (
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
    ParallelizationParametersModel,
    ReportingConfigModel,
    SnapshotsConfigModel,
    StorageConfigModel,
    SummarizeDescriptionsConfigModel,
    TextEmbeddingConfigModel,
    UmapConfigModel,
)

InputModelValidator = TypeAdapter(DefaultConfigParametersInputModel)


def default_config_parameters(
    values: DefaultConfigParametersInputModel | None = None, root_dir: str | None = None
) -> DefaultConfigParametersModel:
    """Load Configuration Parameters from a dictionary."""
    values = values or {}
    root_dir = root_dir or str(Path.cwd())
    env = _make_env(root_dir)
    _token_replace(cast(dict, values))
    InputModelValidator.validate_python(values, strict=True)

    reader = EnvironmentReader(env)

    def hydrate_async_type(input: LLMConfigInputModel, base: AsyncType) -> AsyncType:
        value = input.get(Fragment.async_mode)
        return AsyncType(value) if value else base

    def hydrate_llm_params(
        config: LLMConfigInputModel, base: LLMParametersModel
    ) -> LLMParametersModel:
        with reader.use(config.get("llm")):
            llm_type = reader.str(Fragment.type)
            llm_type = LLMType(llm_type) if llm_type else base.type
            api_key = reader.str(Fragment.api_key) or base.api_key
            api_base = reader.str(Fragment.api_base) or base.api_base
            deployment_name = (
                reader.str(Fragment.deployment_name) or base.deployment_name
            )

            if api_key is None:
                raise ApiKeyMissingError
            if _is_azure(llm_type):
                if api_base is None:
                    raise AzureApiBaseMissingError
                if deployment_name is None:
                    raise AzureDeploymentNameMissingError

            sleep_on_rate_limit = reader.bool(Fragment.sleep_recommendation)
            if sleep_on_rate_limit is None:
                sleep_on_rate_limit = base.sleep_on_rate_limit_recommendation

            return LLMParametersModel(
                api_key=api_key,
                type=llm_type,
                api_base=api_base,
                api_version=reader.str(Fragment.api_version) or base.api_version,
                organization=reader.str("organization") or base.organization,
                proxy=reader.str("proxy") or base.proxy,
                model=reader.str("model") or base.model,
                max_tokens=reader.int(Fragment.max_tokens) or base.max_tokens,
                model_supports_json=reader.bool(Fragment.model_supports_json)
                or base.model_supports_json,
                request_timeout=reader.float(Fragment.request_timeout)
                or base.request_timeout,
                deployment_name=deployment_name,
                tokens_per_minute=reader.int("tokens_per_minute", Fragment.tpm)
                or base.tokens_per_minute,
                requests_per_minute=reader.int("requests_per_minute", Fragment.rpm)
                or base.requests_per_minute,
                max_retries=reader.int(Fragment.max_retries) or base.max_retries,
                max_retry_wait=reader.float(Fragment.max_retry_wait)
                or base.max_retry_wait,
                sleep_on_rate_limit_recommendation=sleep_on_rate_limit,
                concurrent_requests=reader.int(Fragment.concurrent_requests)
                or base.concurrent_requests,
            )

    def hydrate_embeddings_params(
        config: LLMConfigInputModel, base: LLMParametersModel
    ) -> LLMParametersModel:
        with reader.use(config.get("llm")):
            api_key = reader.str(Fragment.api_key) or base.api_key
            api_base = reader.str(Fragment.api_base) or base.api_base
            api_version = reader.str(Fragment.api_version) or base.api_version
            api_organization = reader.str("organization") or base.organization
            api_proxy = reader.str("proxy") or base.proxy
            api_type = reader.str(Fragment.type) or DEFAULT_EMBEDDING_TYPE
            api_type = LLMType(api_type) if api_type else DEFAULT_LLM_TYPE
            deployment_name = reader.str(Fragment.deployment_name)

            if api_key is None:
                raise ApiKeyMissingError(embedding=True)
            if _is_azure(api_type):
                if api_base is None:
                    raise AzureApiBaseMissingError(embedding=True)
                if deployment_name is None:
                    raise AzureDeploymentNameMissingError(embedding=True)

            sleep_on_rate_limit = reader.bool(Fragment.sleep_recommendation)
            if sleep_on_rate_limit is None:
                sleep_on_rate_limit = base.sleep_on_rate_limit_recommendation

            return LLMParametersModel(
                api_key=api_key,
                type=api_type,
                api_base=api_base,
                api_version=api_version,
                organization=api_organization,
                proxy=api_proxy,
                model=reader.str(Fragment.model) or DEFAULT_EMBEDDING_MODEL,
                request_timeout=reader.float(Fragment.request_timeout)
                or DEFAULT_LLM_REQUEST_TIMEOUT,
                deployment_name=deployment_name,
                tokens_per_minute=reader.int("tokens_per_minute", Fragment.tpm)
                or DEFAULT_LLM_TOKENS_PER_MINUTE,
                requests_per_minute=reader.int("requests_per_minute", Fragment.rpm)
                or DEFAULT_LLM_REQUESTS_PER_MINUTE,
                max_retries=reader.int(Fragment.max_retries) or DEFAULT_LLM_MAX_RETRIES,
                max_retry_wait=reader.float(Fragment.max_retry_wait)
                or DEFAULT_LLM_MAX_RETRY_WAIT,
                sleep_on_rate_limit_recommendation=sleep_on_rate_limit,
                concurrent_requests=reader.int(Fragment.concurrent_requests)
                or DEFAULT_LLM_CONCURRENT_REQUESTS,
            )

    def hydrate_parallelization_params(
        config: LLMConfigInputModel, base: ParallelizationParametersModel
    ) -> ParallelizationParametersModel:
        with reader.use(config.get("parallelization")):
            return ParallelizationParametersModel(
                num_threads=reader.int("num_threads", Fragment.thread_count)
                or base.num_threads,
                stagger=reader.float("stagger", Fragment.thread_stagger)
                or base.stagger,
            )

    fallback_oai_key = env("OPENAI_API_KEY", env("AZURE_OPENAI_API_KEY", None))
    fallback_oai_org = env("OPENAI_ORG_ID", None)
    fallback_oai_base = env("OPENAI_BASE_URL", None)
    fallback_oai_version = env("OPENAI_API_VERSION", None)

    with reader.envvar_prefix(Section.graphrag), reader.use(values):
        async_mode = reader.str(Fragment.async_mode)
        async_mode = AsyncType(async_mode) if async_mode else DEFAULT_ASYNC_MODE

        fallback_oai_key = reader.str(Fragment.api_key) or fallback_oai_key
        fallback_oai_org = reader.str(Fragment.api_organization) or fallback_oai_org
        fallback_oai_base = reader.str(Fragment.api_base) or fallback_oai_base
        fallback_oai_version = reader.str(Fragment.api_version) or fallback_oai_version
        fallback_oai_proxy = reader.str(Fragment.api_proxy)

        with reader.envvar_prefix(Section.llm):
            with reader.use(values.get("llm")):
                llm_type = reader.str(Fragment.type)
                llm_type = LLMType(llm_type) if llm_type else DEFAULT_LLM_TYPE
                api_key = reader.str(Fragment.api_key) or fallback_oai_key
                api_organization = (
                    reader.str(Fragment.api_organization) or fallback_oai_org
                )
                api_base = reader.str(Fragment.api_base) or fallback_oai_base
                api_version = reader.str(Fragment.api_version) or fallback_oai_version
                api_proxy = reader.str(Fragment.api_proxy) or fallback_oai_proxy
                deployment_name = reader.str(Fragment.deployment_name)

                if api_key is None:
                    raise ApiKeyMissingError
                if _is_azure(llm_type):
                    if api_base is None:
                        raise AzureApiBaseMissingError
                    if deployment_name is None:
                        raise AzureDeploymentNameMissingError

                sleep_on_rate_limit = reader.bool(Fragment.sleep_recommendation)
                if sleep_on_rate_limit is None:
                    sleep_on_rate_limit = DEFAULT_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION

                llm_model = LLMParametersModel(
                    api_key=api_key,
                    api_base=api_base,
                    api_version=api_version,
                    organization=api_organization,
                    proxy=api_proxy,
                    type=llm_type,
                    model=reader.str(Fragment.model) or DEFAULT_LLM_MODEL,
                    max_tokens=reader.int(Fragment.max_tokens)
                    or DEFAULT_LLM_MAX_TOKENS,
                    model_supports_json=reader.bool(Fragment.model_supports_json),
                    request_timeout=reader.float(Fragment.request_timeout)
                    or DEFAULT_LLM_REQUEST_TIMEOUT,
                    deployment_name=deployment_name,
                    tokens_per_minute=reader.int(Fragment.tpm)
                    or DEFAULT_LLM_TOKENS_PER_MINUTE,
                    requests_per_minute=reader.int(Fragment.rpm)
                    or DEFAULT_LLM_REQUESTS_PER_MINUTE,
                    max_retries=reader.int(Fragment.max_retries)
                    or DEFAULT_LLM_MAX_RETRIES,
                    max_retry_wait=reader.float(Fragment.max_retry_wait)
                    or DEFAULT_LLM_MAX_RETRY_WAIT,
                    sleep_on_rate_limit_recommendation=sleep_on_rate_limit,
                    concurrent_requests=reader.int(Fragment.concurrent_requests)
                    or DEFAULT_LLM_CONCURRENT_REQUESTS,
                )
            with reader.use(values.get("parallelization")):
                llm_parallelization_model = ParallelizationParametersModel(
                    stagger=reader.float("stagger", Fragment.thread_stagger)
                    or DEFAULT_PARALLELIZATION_STAGGER,
                    num_threads=reader.int("num_threads", Fragment.thread_count)
                    or DEFAULT_PARALLELIZATION_NUM_THREADS,
                )
        embeddings_config = values.get("embeddings") or {}
        with reader.envvar_prefix(Section.embedding), reader.use(embeddings_config):
            embeddings_target = reader.str("target")
            embeddings_model = TextEmbeddingConfigModel(
                llm=hydrate_embeddings_params(embeddings_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    embeddings_config, llm_parallelization_model
                ),
                async_mode=hydrate_async_type(embeddings_config, async_mode),
                target=TextEmbeddingTarget(embeddings_target)
                if embeddings_target
                else DEFAULT_EMBEDDING_TARGET,
                batch_size=reader.int("batch_size") or DEFAULT_EMBEDDING_BATCH_SIZE,
                batch_max_tokens=reader.int("batch_max_tokens")
                or DEFAULT_EMBEDDING_BATCH_MAX_TOKENS,
                skip=reader.list("skip") or [],
            )
        with (
            reader.envvar_prefix(Section.node2vec),
            reader.use(values.get("embed_graph")),
        ):
            embed_graph_model = EmbedGraphConfigModel(
                enabled=reader.bool(Fragment.enabled) or DEFAULT_NODE2VEC_IS_ENABLED,
                num_walks=reader.int("num_walks") or DEFAULT_NODE2VEC_NUM_WALKS,
                walk_length=reader.int("walk_length") or DEFAULT_NODE2VEC_WALK_LENGTH,
                window_size=reader.int("window_size") or DEFAULT_NODE2VEC_WINDOW_SIZE,
                iterations=reader.int("iterations") or DEFAULT_NODE2VEC_ITERATIONS,
                random_seed=reader.int("random_seed") or DEFAULT_NODE2VEC_RANDOM_SEED,
            )
        with reader.envvar_prefix(Section.input), reader.use(values.get("input")):
            input_type = reader.str(Fragment.type)
            storage_type = reader.str("storage_type")
            input_model = InputConfigModel(
                type=PipelineInputType(input_type)
                if input_type
                else DEFAULT_INPUT_TYPE,
                storage_type=PipelineInputStorageType(storage_type)
                if storage_type
                else DEFAULT_INPUT_STORAGE_TYPE,
                file_encoding=reader.str("file_encoding", Fragment.encoding)
                or DEFAULT_INPUT_FILE_ENCODING,
                base_dir=reader.str(Fragment.base_dir) or DEFAULT_INPUT_BASE_DIR,
                file_pattern=reader.str("file_pattern")
                or (
                    DEFAULT_INPUT_TEXT_PATTERN
                    if input_type == PipelineInputType.text
                    else DEFAULT_INPUT_CSV_PATTERN
                ),
                source_column=reader.str("source_column"),
                timestamp_column=reader.str("timestamp_column"),
                timestamp_format=reader.str("timestamp_format"),
                text_column=reader.str("text_column") or DEFAULT_INPUT_TEXT_COLUMN,
                title_column=reader.str("title_column"),
                document_attribute_columns=reader.list("document_attribute_columns")
                or [],
                connection_string=reader.str(Fragment.conn_string),
                container_name=reader.str(Fragment.container_name),
            )
        with reader.envvar_prefix(Section.cache), reader.use(values.get("cache")):
            c_type = reader.str(Fragment.type)
            cache_model = CacheConfigModel(
                type=PipelineCacheType(c_type) if c_type else DEFAULT_CACHE_TYPE,
                connection_string=reader.str(Fragment.conn_string),
                container_name=reader.str(Fragment.container_name),
                base_dir=reader.str(Fragment.base_dir) or DEFAULT_CACHE_BASE_DIR,
            )
        with (
            reader.envvar_prefix(Section.reporting),
            reader.use(values.get("reporting")),
        ):
            r_type = reader.str(Fragment.type)
            reporting_model = ReportingConfigModel(
                type=PipelineReportingType(r_type)
                if r_type
                else DEFAULT_REPORTING_TYPE,
                connection_string=reader.str(Fragment.conn_string),
                container_name=reader.str(Fragment.container_name),
                base_dir=reader.str(Fragment.base_dir) or DEFAULT_REPORTING_BASE_DIR,
            )
        with reader.envvar_prefix(Section.storage), reader.use(values.get("storage")):
            s_type = reader.str(Fragment.type)
            storage_model = StorageConfigModel(
                type=PipelineStorageType(s_type) if s_type else DEFAULT_STORAGE_TYPE,
                connection_string=reader.str(Fragment.conn_string),
                container_name=reader.str(Fragment.container_name),
                base_dir=reader.str(Fragment.base_dir) or DEFAULT_STORAGE_BASE_DIR,
            )
        with reader.envvar_prefix(Section.chunk), reader.use(values.get("chunks")):
            chunks_model = ChunkingConfigModel(
                size=reader.int("size") or DEFAULT_CHUNK_SIZE,
                overlap=reader.int("overlap") or DEFAULT_CHUNK_OVERLAP,
                group_by_columns=reader.list("group_by_columns", "BY_COLUMNS")
                or DEFAULT_CHUNK_GROUP_BY_COLUMNS,
            )
        with (
            reader.envvar_prefix(Section.snapshot),
            reader.use(values.get("snapshots")),
        ):
            snapshots_model = SnapshotsConfigModel(
                graphml=reader.bool("graphml") or DEFAULT_SNAPSHOTS_GRAPHML,
                raw_entities=reader.bool("raw_entities")
                or DEFAULT_SNAPSHOTS_RAW_ENTITIES,
                top_level_nodes=reader.bool("top_level_nodes")
                or DEFAULT_SNAPSHOTS_TOP_LEVEL_NODES,
            )
        with reader.envvar_prefix(Section.umap), reader.use(values.get("umap")):
            umap_model = UmapConfigModel(
                enabled=reader.bool(Fragment.enabled) or DEFAULT_UMAP_ENABLED,
            )

        entity_extraction_config = values.get("entity_extraction") or {}
        with (
            reader.envvar_prefix(Section.entity_extraction),
            reader.use(entity_extraction_config),
        ):
            entity_extraction_model = EntityExtractionConfigModel(
                llm=hydrate_llm_params(entity_extraction_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    entity_extraction_config, llm_parallelization_model
                ),
                async_mode=hydrate_async_type(entity_extraction_config, async_mode),
                entity_types=reader.list("entity_types")
                or DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
                max_gleanings=reader.int(Fragment.max_gleanings)
                or DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS,
                prompt=reader.str("prompt", Fragment.prompt_file),
            )

        claim_extraction_config = values.get("claim_extraction") or {}
        with (
            reader.envvar_prefix(Section.claim_extraction),
            reader.use(claim_extraction_config),
        ):
            claim_extraction_model = ClaimExtractionConfigModel(
                llm=hydrate_llm_params(claim_extraction_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    claim_extraction_config, llm_parallelization_model
                ),
                async_mode=hydrate_async_type(claim_extraction_config, async_mode),
                description=reader.str("description") or DEFAULT_CLAIM_DESCRIPTION,
                prompt=reader.str("prompt", Fragment.prompt_file),
                max_gleanings=reader.int(Fragment.max_gleanings)
                or DEFAULT_CLAIM_MAX_GLEANINGS,
            )

        community_report_config = values.get("community_reports") or {}
        with (
            reader.envvar_prefix(Section.community_report),
            reader.use(community_report_config),
        ):
            community_reports_model = CommunityReportsConfigModel(
                llm=hydrate_llm_params(community_report_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    community_report_config, llm_parallelization_model
                ),
                async_mode=hydrate_async_type(community_report_config, async_mode),
                prompt=reader.str("prompt", Fragment.prompt_file),
                max_length=reader.int(Fragment.max_length)
                or DEFAULT_COMMUNITY_REPORT_MAX_LENGTH,
                max_input_length=reader.int("max_input_length")
                or DEFAULT_COMMUNITY_REPORT_MAX_INPUT_LENGTH,
            )

        summarize_description_config = values.get("summarize_descriptions") or {}
        with (
            reader.envvar_prefix(Section.summarize_descriptions),
            reader.use(values.get("summarize_descriptions")),
        ):
            summarize_descriptions_model = SummarizeDescriptionsConfigModel(
                llm=hydrate_llm_params(summarize_description_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    summarize_description_config, llm_parallelization_model
                ),
                async_mode=hydrate_async_type(summarize_description_config, async_mode),
                prompt=reader.str("prompt", Fragment.prompt_file),
                max_length=reader.int(Fragment.max_length)
                or DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
            )

        with reader.use(values.get("cluster_graph")):
            cluster_graph_model = ClusterGraphConfigModel(
                max_cluster_size=reader.int("max_cluster_size")
                or DEFAULT_MAX_CLUSTER_SIZE
            )

        encoding_model = reader.str(Fragment.encoding_model) or DEFAULT_ENCODING_MODEL
        skip_workflows = reader.list("skip_workflows") or []

    return DefaultConfigParametersModel(
        root_dir=root_dir,
        llm=llm_model,
        parallelization=llm_parallelization_model,
        async_mode=async_mode,
        embeddings=embeddings_model,
        embed_graph=embed_graph_model,
        reporting=reporting_model,
        storage=storage_model,
        cache=cache_model,
        input=input_model,
        chunks=chunks_model,
        snapshots=snapshots_model,
        entity_extraction=entity_extraction_model,
        claim_extraction=claim_extraction_model,
        community_reports=community_reports_model,
        summarize_descriptions=summarize_descriptions_model,
        umap=umap_model,
        cluster_graph=cluster_graph_model,
        encoding_model=encoding_model,
        skip_workflows=skip_workflows,
    )


class Fragment(str, Enum):
    """Configuration Fragments."""

    api_base = "API_BASE"
    api_key = "API_KEY"
    api_version = "API_VERSION"
    api_organization = "API_ORGANIZATION"
    api_proxy = "API_PROXY"
    async_mode = "ASYNC_MODE"
    concurrent_requests = "CONCURRENT_REQUESTS"
    conn_string = "CONNECTION_STRING"
    container_name = "CONTAINER_NAME"
    deployment_name = "DEPLOYMENT_NAME"
    description = "DESCRIPTION"
    enabled = "ENABLED"
    encoding = "ENCODING"
    encoding_model = "ENCODING_MODEL"
    max_gleanings = "MAX_GLEANINGS"
    max_length = "MAX_LENGTH"
    max_retries = "MAX_RETRIES"
    max_retry_wait = "MAX_RETRY_WAIT"
    max_tokens = "MAX_TOKENS"
    model = "MODEL"
    model_supports_json = "MODEL_SUPPORTS_JSON"
    prompt_file = "PROMPT_FILE"
    request_timeout = "REQUEST_TIMEOUT"
    rpm = "RPM"
    sleep_recommendation = "SLEEP_ON_RATE_LIMIT_RECOMMENDATION"
    thread_count = "THREAD_COUNT"
    thread_stagger = "THREAD_STAGGER"
    tpm = "TPM"
    type = "TYPE"
    base_dir = "BASE_DIR"


class Section(str, Enum):
    """Configuration Sections."""

    base = "BASE"
    cache = "CACHE"
    chunk = "CHUNK"
    claim_extraction = "CLAIM_EXTRACTION"
    community_report = "COMMUNITY_REPORT"
    embedding = "EMBEDDING"
    entity_extraction = "ENTITY_EXTRACTION"
    graphrag = "GRAPHRAG"
    input = "INPUT"
    llm = "LLM"
    node2vec = "NODE2VEC"
    reporting = "REPORTING"
    snapshot = "SNAPSHOT"
    storage = "STORAGE"
    summarize_descriptions = "SUMMARIZE_DESCRIPTIONS"
    umap = "UMAP"


def _is_azure(llm_type: LLMType | None) -> bool:
    return (
        llm_type == LLMType.AzureOpenAI
        or llm_type == LLMType.AzureOpenAIChat
        or llm_type == LLMType.AzureOpenAIEmbedding
    )


def _make_env(root_dir: str) -> Env:
    read_dotenv(root_dir)
    env = Env(expand_vars=True)
    env.read_env()
    return env


def _token_replace(data: dict):
    """Replace env-var tokens in a dictionary object."""
    for key, value in data.items():
        if isinstance(value, dict):
            _token_replace(value)
        elif isinstance(value, str):
            data[key] = os.path.expandvars(value)
