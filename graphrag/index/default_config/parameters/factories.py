# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""
import os
from enum import Enum
from pathlib import Path

from datashaper import AsyncType
from environs import Env

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
from .input_models import (
    CacheConfigInputModel,
    ChunkingConfigInputModel,
    ClaimExtractionConfigInputModel,
    ClusterGraphConfigInputModel,
    CommunityReportsConfigInputModel,
    DefaultConfigParametersInputModel,
    EmbedGraphConfigInputModel,
    EntityExtractionConfigInputModel,
    InputConfigInputModel,
    LLMConfigInputModel,
    LLMParametersInputModel,
    ParallelizationParametersInputModel,
    ReportingConfigInputModel,
    SnapshotsConfigInputModel,
    StorageConfigInputModel,
    SummarizeDescriptionsConfigInputModel,
    TextEmbeddingConfigInputModel,
    UmapConfigInputModel,
)
from .models import (
    CacheConfigModel,
    ChunkingConfigModel,
    ClaimExtractionConfigModel,
    ClusterGraphConfigModel,
    CommunityReportsConfigModel,
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
from .models.default_config_parameters_model import DefaultConfigParametersModel

LLM_KEY_REQUIRED = "API Key is required for Completion API. Please set either the OPENAI_API_KEY, GRAPHRAG_API_KEY or GRAPHRAG_LLM_API_KEY environment variable."
EMBEDDING_KEY_REQUIRED = "API Key is required for Embedding API. Please set either the OPENAI_API_KEY, GRAPHRAG_API_KEY or GRAPHRAG_EMBEDDING_API_KEY environment variable."
AZURE_LLM_DEPLOYMENT_NAME_REQUIRED = (
    "GRAPHRAG_LLM_MODEL or GRAPHRAG_LLM_DEPLOYMENT_NAME is required for Azure OpenAI."
)
AZURE_LLM_API_BASE_REQUIRED = (
    "GRAPHRAG_API_BASE or GRAPHRAG_LLM_API_BASE is required for Azure OpenAI."
)
AZURE_EMBEDDING_DEPLOYMENT_NAME_REQUIRED = "GRAPHRAG_EMBEDDING_MODEL or GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME is required for Azure OpenAI."
AZURE_EMBEDDING_API_BASE_REQUIRED = (
    "GRAPHRAG_API_BASE or GRAPHRAG_EMBEDDING_API_BASE is required for Azure OpenAI."
)


def default_config_parameters(
    values: DefaultConfigParametersInputModel, root_dir: str | None
) -> DefaultConfigParametersModel:
    """Load Configuration Parameters from a dictionary."""
    root_dir = root_dir or str(Path.cwd())
    _make_env(root_dir)

    def traverse_dict(data):
        for key, value in data.items():
            if isinstance(value, dict):
                traverse_dict(value)
            elif (
                isinstance(value, str)
                and value.startswith("${")
                and value.endswith("}")
            ):
                data[key] = os.path.expandvars(value)

    traverse_dict(values)

    def _int(value: int | str | None, default_value: int | None = None) -> int | None:
        return int(value) if value else default_value

    def _bool(
        value: bool | str | None, default_value: bool | None = None
    ) -> bool | None:
        return bool(value) if value else default_value

    def _float(
        value: float | str | None, default_value: float | None = None
    ) -> float | None:
        return float(value) if value else default_value

    def _list(
        value: list | str | None, default_value: list | None = None
    ) -> list | None:
        return (
            value
            if isinstance(value, list)
            else [s.strip() for s in value.split(",")]
            if value
            else default_value
        )

    def _async_type(input: LLMConfigInputModel) -> AsyncType:
        value = input.get("async_mode")
        return AsyncType(value) if value else DEFAULT_ASYNC_MODE

    def hydrate_llm_params(config: LLMConfigInputModel) -> LLMParametersModel:
        llm_settings = config.get("llm") or {}
        root_settings = values.get("llm") or {}

        def _lookup(k: str):
            return llm_settings.get(k) or root_settings.get(k)

        llm_type = _lookup("type")
        api_key = _lookup("api_key")
        if api_key is None:
            raise ValueError(LLM_KEY_REQUIRED)

        return LLMParametersModel(
            api_key=api_key,
            type=LLMType(llm_type) if llm_type else DEFAULT_LLM_TYPE,
            api_base=_lookup("api_base"),
            api_version=_lookup("api_version"),
            organization=_lookup("organization"),
            proxy=_lookup("proxy"),
            model=_lookup("model") or DEFAULT_LLM_MODEL,
            max_tokens=_int(_lookup("max_tokens"), DEFAULT_LLM_MAX_TOKENS),
            model_supports_json=_bool(_lookup("model_supports_json")),
            request_timeout=_float(_lookup("request_timeout"))
            or DEFAULT_LLM_REQUEST_TIMEOUT,
            deployment_name=_lookup("deployment_name"),
            tokens_per_minute=_int(_lookup("tokens_per_minute"))
            or DEFAULT_LLM_TOKENS_PER_MINUTE,
            requests_per_minute=_int(_lookup("requests_per_minute"))
            or DEFAULT_LLM_REQUESTS_PER_MINUTE,
            max_retries=_int(_lookup("max_retries")) or DEFAULT_LLM_MAX_RETRIES,
            max_retry_wait=_float(_lookup("max_retry_wait"))
            or DEFAULT_LLM_MAX_RETRY_WAIT,
            sleep_on_rate_limit_recommendation=_bool(
                _lookup("sleep_on_rate_limit_recommendation"),
            )
            or DEFAULT_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION,
            concurrent_requests=_int(_lookup("concurrent_requests"))
            or DEFAULT_LLM_CONCURRENT_REQUESTS,
        )

    def hydrate_embeddings_params(config: LLMConfigInputModel) -> LLMParametersModel:
        llm_settings = config.get("llm") or {}
        root_settings = values.get("llm") or {}

        def _lookup(k: str):
            return llm_settings.get(k) or root_settings.get(k)

        llm_type = _lookup("type")
        api_key = _lookup("api_key")
        if api_key is None:
            raise ValueError(LLM_KEY_REQUIRED)

        return LLMParametersModel(
            api_key=api_key,
            type=LLMType(llm_type) if llm_type else DEFAULT_EMBEDDING_TYPE,
            api_base=_lookup("api_base"),
            api_version=_lookup("api_version"),
            organization=_lookup("organization"),
            proxy=_lookup("proxy"),
            model=_lookup("model") or DEFAULT_EMBEDDING_MODEL,
            model_supports_json=_bool(_lookup("model_supports_json")),
            request_timeout=_float(
                _lookup("request_timeout"),
            )
            or DEFAULT_LLM_REQUEST_TIMEOUT,
            deployment_name=_lookup("deployment_name"),
            tokens_per_minute=_int(_lookup("tokens_per_minute"))
            or DEFAULT_LLM_TOKENS_PER_MINUTE,
            requests_per_minute=_int(_lookup("requests_per_minute"))
            or DEFAULT_LLM_REQUESTS_PER_MINUTE,
            max_retries=_int(_lookup("max_retries")) or DEFAULT_LLM_MAX_RETRIES,
            max_retry_wait=_float(_lookup("max_retry_wait"))
            or DEFAULT_LLM_MAX_RETRY_WAIT,
            sleep_on_rate_limit_recommendation=_bool(
                _lookup("sleep_on_rate_limit_recommendation")
            )
            or DEFAULT_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION,
            concurrent_requests=_int(_lookup("concurrent_requests"))
            or DEFAULT_LLM_CONCURRENT_REQUESTS,
        )

    def hydrate_parallelization_params(
        config: LLMConfigInputModel,
    ) -> ParallelizationParametersModel:
        settings = config.get("parallelization") or {}
        root_settings = values.get("parallelization") or {}

        def lookup(key: str) -> str | None:
            return settings.get(key) or root_settings.get(key)

        return ParallelizationParametersModel(
            num_threads=_int(
                lookup("num_threads"),
            )
            or DEFAULT_PARALLELIZATION_NUM_THREADS,
            stagger=_float(lookup("thread_stagger")) or DEFAULT_PARALLELIZATION_STAGGER,
        )

    embeddings_config: TextEmbeddingConfigInputModel = values.get("embeddings") or {}
    embed_graph_config: EmbedGraphConfigInputModel = values.get("embed_graph") or {}
    reporting_config: ReportingConfigInputModel = values.get("reporting") or {}
    storage_config: StorageConfigInputModel = values.get("storage") or {}
    cache_config: CacheConfigInputModel = values.get("cache") or {}
    input_config: InputConfigInputModel = values.get("input") or {}
    chunk_config: ChunkingConfigInputModel = values.get("chunks") or {}
    snapshots_config: SnapshotsConfigInputModel = values.get("snapshots") or {}
    entity_extraction_config: EntityExtractionConfigInputModel = (
        values.get("entity_extraction") or {}
    )
    claim_extraction_config: ClaimExtractionConfigInputModel = (
        values.get("claim_extraction") or {}
    )
    community_report_config: CommunityReportsConfigInputModel = (
        values.get("community_reports") or {}
    )
    summarize_description_config: SummarizeDescriptionsConfigInputModel = (
        values.get("summarize_descriptions") or {}
    )
    umap_config: UmapConfigInputModel = values.get("umap") or {}
    cluster_graph_config: ClusterGraphConfigInputModel = (
        values.get("cluster_graph") or {}
    )

    reporting_type = reporting_config.get("type")
    reporting_type = (
        PipelineReportingType(reporting_type)
        if reporting_type
        else DEFAULT_REPORTING_TYPE
    )
    storage_type = storage_config.get("type")
    storage_type = (
        PipelineStorageType(storage_type) if storage_type else DEFAULT_STORAGE_TYPE
    )
    cache_type = cache_config.get("type")
    cache_type = PipelineCacheType(cache_type) if cache_type else DEFAULT_CACHE_TYPE
    input_type = input_config.get("type")
    input_type = PipelineInputType(input_type) if input_type else DEFAULT_INPUT_TYPE
    input_storage_type = input_config.get("storage_type")
    input_storage_type = (
        PipelineInputStorageType(input_storage_type)
        if input_storage_type
        else DEFAULT_INPUT_STORAGE_TYPE
    )
    embeddings_target = embeddings_config.get("target")
    embeddings_target = (
        TextEmbeddingTarget(embeddings_target)
        if embeddings_target
        else DEFAULT_EMBEDDING_TARGET
    )
    file_pattern = input_config.get("file_pattern") or (
        DEFAULT_INPUT_TEXT_PATTERN
        if input_type == PipelineInputType.text
        else DEFAULT_INPUT_CSV_PATTERN
    )

    return DefaultConfigParametersModel(
        root_dir=root_dir,
        llm=hydrate_llm_params(values),
        parallelization=hydrate_parallelization_params(values),
        async_mode=_async_type(values),
        embeddings=TextEmbeddingConfigModel(
            llm=hydrate_embeddings_params(embeddings_config),
            parallelization=hydrate_parallelization_params(embeddings_config),
            async_mode=_async_type(embeddings_config),
            target=embeddings_target,
            batch_size=_int(embeddings_config.get("batch_size"))
            or DEFAULT_EMBEDDING_BATCH_SIZE,
            batch_max_tokens=_int(
                embeddings_config.get("batch_max_tokens"),
            )
            or DEFAULT_EMBEDDING_BATCH_MAX_TOKENS,
            skip=_list(embeddings_config.get("skip")) or [],
        ),
        embed_graph=EmbedGraphConfigModel(
            is_enabled=_bool(embed_graph_config.get("enabled"))
            or DEFAULT_NODE2VEC_IS_ENABLED,
            num_walks=_int(
                embed_graph_config.get("num_walks"),
            )
            or DEFAULT_NODE2VEC_NUM_WALKS,
            walk_length=_int(
                embed_graph_config.get("walk_length"),
            )
            or DEFAULT_NODE2VEC_WALK_LENGTH,
            window_size=_int(
                embed_graph_config.get("window_size"),
            )
            or DEFAULT_NODE2VEC_WINDOW_SIZE,
            iterations=_int(
                embed_graph_config.get("iterations"),
            )
            or DEFAULT_NODE2VEC_ITERATIONS,
            random_seed=_int(
                embed_graph_config.get("random_seed"),
            )
            or DEFAULT_NODE2VEC_RANDOM_SEED,
        ),
        reporting=ReportingConfigModel(
            type=reporting_type,
            connection_string=reporting_config.get("connection_string"),
            container_name=reporting_config.get("container_name"),
            base_dir=reporting_config.get("base_dir") or DEFAULT_REPORTING_BASE_DIR,
        ),
        storage=StorageConfigModel(
            type=storage_type,
            connection_string=storage_config.get("connection_string"),
            container_name=storage_config.get("container_name"),
            base_dir=storage_config.get("base_dir") or DEFAULT_STORAGE_BASE_DIR,
        ),
        cache=CacheConfigModel(
            type=cache_type,
            connection_string=cache_config.get("connection_string"),
            container_name=cache_config.get("container_name"),
            base_dir=cache_config.get("base_dir") or DEFAULT_CACHE_BASE_DIR,
        ),
        input=InputConfigModel(
            type=input_type,
            storage_type=input_storage_type,
            file_encoding=input_config.get("file_encoding")
            or DEFAULT_INPUT_FILE_ENCODING,
            base_dir=input_config.get("base_dir") or DEFAULT_INPUT_BASE_DIR,
            file_pattern=file_pattern,
            source_column=input_config.get("source_column"),
            timestamp_column=input_config.get("timestamp_column"),
            timestamp_format=input_config.get("timestamp_format"),
            text_column=input_config.get("text_column") or DEFAULT_INPUT_TEXT_COLUMN,
            title_column=input_config.get("title_column"),
            document_attribute_columns=_list(
                input_config.get("document_attribute_columns")
            )
            or [],
        ),
        chunks=ChunkingConfigModel(
            size=_int(
                chunk_config.get("size"),
            )
            or DEFAULT_CHUNK_SIZE,
            overlap=_int(
                chunk_config.get("overlap"),
            )
            or DEFAULT_CHUNK_OVERLAP,
            group_by_columns=_list(
                chunk_config.get("group_by_columns"),
            )
            or DEFAULT_CHUNK_GROUP_BY_COLUMNS,
        ),
        snapshots=SnapshotsConfigModel(
            graphml=_bool(
                snapshots_config.get("graphml"),
            )
            or DEFAULT_SNAPSHOTS_GRAPHML,
            raw_entities=_bool(
                snapshots_config.get("raw_entities"),
            )
            or DEFAULT_SNAPSHOTS_RAW_ENTITIES,
            top_level_nodes=_bool(
                snapshots_config.get("top_level_nodes"),
            )
            or DEFAULT_SNAPSHOTS_TOP_LEVEL_NODES,
        ),
        entity_extraction=EntityExtractionConfigModel(
            llm=hydrate_llm_params(entity_extraction_config),
            parallelization=hydrate_parallelization_params(entity_extraction_config),
            async_mode=_async_type(entity_extraction_config),
            entity_types=_list(
                entity_extraction_config.get("entity_types"),
            )
            or DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
            max_gleanings=_int(
                entity_extraction_config.get("max_gleanings"),
            )
            or DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS,
            prompt=entity_extraction_config.get("prompt_file"),
        ),
        claim_extraction=ClaimExtractionConfigModel(
            llm=hydrate_llm_params(claim_extraction_config),
            parallelization=hydrate_parallelization_params(claim_extraction_config),
            async_mode=_async_type(claim_extraction_config),
            description=claim_extraction_config.get("description")
            or DEFAULT_CLAIM_DESCRIPTION,
            prompt=claim_extraction_config.get("prompt_file"),
            max_gleanings=_int(claim_extraction_config.get("max_gleanings"))
            or DEFAULT_CLAIM_MAX_GLEANINGS,
        ),
        community_reports=CommunityReportsConfigModel(
            llm=hydrate_llm_params(community_report_config),
            parallelization=hydrate_parallelization_params(community_report_config),
            async_mode=_async_type(community_report_config),
            prompt=community_report_config.get("prompt_file"),
            max_length=_int(
                community_report_config.get("max_length"),
            )
            or DEFAULT_COMMUNITY_REPORT_MAX_LENGTH,
            max_input_length=_int(
                community_report_config.get("max_input_length"),
            )
            or DEFAULT_COMMUNITY_REPORT_MAX_INPUT_LENGTH,
        ),
        summarize_descriptions=SummarizeDescriptionsConfigModel(
            llm=hydrate_llm_params(summarize_description_config),
            parallelization=hydrate_parallelization_params(
                summarize_description_config
            ),
            async_mode=_async_type(summarize_description_config),
            prompt=summarize_description_config.get("prompt_file"),
            max_length=_int(
                summarize_description_config.get("max_length"),
            )
            or DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
        ),
        umap=UmapConfigModel(
            enabled=_bool(umap_config.get("enabled")) or DEFAULT_UMAP_ENABLED,
        ),
        cluster_graph=ClusterGraphConfigModel(
            max_cluster_size=_int(cluster_graph_config.get("max_cluster_size"))
            or DEFAULT_MAX_CLUSTER_SIZE,
        ),
        encoding_model=values.get("encoding_model") or DEFAULT_ENCODING_MODEL,
        skip_workflows=_list(values.get("skip_workflows")) or [],
    )


def default_config_parameters_from_env_vars(
    root_dir: str | None,
) -> DefaultConfigParametersModel:
    """Load Configuration Parameters from environment variables."""
    root_dir = root_dir or str(Path.cwd())
    env = _make_env(root_dir)

    def _key(key: str | Fragment) -> str | None:
        return key.value if isinstance(key, Fragment) else key

    def _str(key: str | Fragment, default_value: str | None = None) -> str | None:
        return env(_key(key), default_value)

    def _int(key: str | Fragment, default_value: int | None = None) -> int | None:
        return env.int(_key(key), default_value)

    def _bool(key: str | Fragment, default_value: bool | None = None) -> bool | None:
        return env.bool(_key(key), default_value)

    def _float(key: str | Fragment, default_value: float | None = None) -> float | None:
        return env.float(_key(key), default_value)

    def section(key: Section):
        return env.prefixed(f"{key.value}_")

    fallback_oai_key = _str("OPENAI_API_KEY", _str("AZURE_OPENAI_API_KEY"))
    fallback_oai_org = _str("OPENAI_ORG_ID")
    fallback_oai_url = _str("OPENAI_BASE_URL")
    fallback_oai_version = _str("OPENAI_API_VERSION")

    with section(Section.graphrag):
        _api_key = _str(Fragment.api_key, fallback_oai_key)
        _api_base = _str(Fragment.api_base, fallback_oai_url)
        _api_version = _str(Fragment.api_version, fallback_oai_version)
        _organization = _str(Fragment.api_organization, fallback_oai_org)
        _proxy = _str(Fragment.api_proxy)

        with section(Section.llm):
            api_key = _str(Fragment.api_key, _api_key or fallback_oai_key)
            if api_key is None:
                raise ValueError(LLM_KEY_REQUIRED)
            llm_type = _str(Fragment.type)
            llm_type = LLMType(llm_type) if llm_type else None
            deployment_name = _str(Fragment.deployment_name)
            model = _str(Fragment.model)

            is_azure = _is_azure(llm_type)
            api_base = _str(Fragment.api_base, _api_base)
            if is_azure and deployment_name is None and model is None:
                raise ValueError(AZURE_LLM_DEPLOYMENT_NAME_REQUIRED)
            if is_azure and api_base is None:
                raise ValueError(AZURE_LLM_API_BASE_REQUIRED)

            llm_parameters = LLMParametersInputModel(
                api_key=api_key,
                type=llm_type,
                model=model,
                max_tokens=_int(Fragment.max_tokens),
                model_supports_json=_bool(Fragment.model_supports_json),
                request_timeout=_float(Fragment.request_timeout),
                api_base=api_base,
                api_version=_str(Fragment.api_version, _api_version),
                organization=_str(Fragment.api_organization, _organization),
                proxy=_str(Fragment.api_proxy, _proxy),
                deployment_name=deployment_name,
                tokens_per_minute=_int(Fragment.tpm),
                requests_per_minute=_int(Fragment.rpm),
                max_retries=_int(Fragment.max_retries),
                max_retry_wait=_float(Fragment.max_retry_wait),
                sleep_on_rate_limit_recommendation=_bool(Fragment.sleep_recommendation),
                concurrent_requests=_int(Fragment.concurrent_requests),
            )
            llm_parallelization = ParallelizationParametersInputModel(
                stagger=_float(Fragment.thread_stagger),
                num_threads=_int(Fragment.thread_count),
            )

        with section(Section.embedding):
            api_key = _str(Fragment.api_key, _api_key)
            if api_key is None:
                raise ValueError(EMBEDDING_KEY_REQUIRED)

            embedding_target = _str("TARGET")
            embedding_target = (
                TextEmbeddingTarget(embedding_target) if embedding_target else None
            )
            async_mode = _str(Fragment.async_mode)
            async_mode_enum = AsyncType(async_mode) if async_mode else None
            deployment_name = _str(Fragment.deployment_name)
            model = _str(Fragment.model)
            llm_type = _str(Fragment.type)
            llm_type = LLMType(llm_type) if llm_type else None
            is_azure = _is_azure(llm_type)
            api_base = _str(Fragment.api_base, _api_base)

            if is_azure and deployment_name is None and model is None:
                raise ValueError(AZURE_EMBEDDING_DEPLOYMENT_NAME_REQUIRED)
            if is_azure and api_base is None:
                raise ValueError(AZURE_EMBEDDING_API_BASE_REQUIRED)

            text_embeddings = TextEmbeddingConfigInputModel(
                parallelization=ParallelizationParametersInputModel(
                    stagger=_float(Fragment.thread_stagger),
                    num_threads=_int(Fragment.thread_count),
                ),
                async_mode=async_mode_enum,
                target=embedding_target,
                batch_size=_int("BATCH_SIZE"),
                batch_max_tokens=_int("BATCH_MAX_TOKENS"),
                skip=_array_string("SKIP"),
                llm=LLMParametersInputModel(
                    api_key=_str(Fragment.api_key, _api_key),
                    type=llm_type,
                    model=model,
                    request_timeout=_float(Fragment.request_timeout),
                    api_base=api_base,
                    api_version=_str(Fragment.api_version, _api_version),
                    organization=_str(Fragment.api_organization, _organization),
                    proxy=_str(Fragment.api_proxy, _proxy),
                    deployment_name=deployment_name,
                    tokens_per_minute=_int(Fragment.tpm),
                    requests_per_minute=_int(Fragment.rpm),
                    max_retries=_int(Fragment.max_retries),
                    max_retry_wait=_float(Fragment.max_retry_wait),
                    sleep_on_rate_limit_recommendation=_bool(
                        Fragment.sleep_recommendation
                    ),
                    concurrent_requests=_int(Fragment.concurrent_requests),
                ),
            )

        with section(Section.node2vec):
            embed_graph = EmbedGraphConfigInputModel(
                is_enabled=_bool(Fragment.enabled),
                num_walks=_int("NUM_WALKS"),
                walk_length=_int("WALK_LENGTH"),
                window_size=_int("WINDOW_SIZE"),
                iterations=_int("ITERATIONS"),
                random_seed=_int("RANDOM_SEED"),
            )
        with section(Section.reporting):
            reporting_type = _str(Fragment.type)
            reporting_type = (
                PipelineReportingType(reporting_type) if reporting_type else None
            )
            reporting = ReportingConfigInputModel(
                type=reporting_type,
                connection_string=_str(Fragment.conn_string),
                container_name=_str(Fragment.container_name),
                base_dir=_str(Fragment.base_dir),
            )
        with section(Section.storage):
            storage_type = _str(Fragment.type)
            storage_type = PipelineStorageType(storage_type) if storage_type else None
            storage = StorageConfigInputModel(
                type=storage_type,
                connection_string=_str(Fragment.conn_string),
                container_name=_str(Fragment.container_name),
                base_dir=_str(Fragment.base_dir),
            )
        with section(Section.cache):
            cache_type = _str(Fragment.type)
            cache_type = PipelineCacheType(cache_type) if cache_type else None
            cache = CacheConfigInputModel(
                type=cache_type,
                connection_string=_str(Fragment.conn_string),
                container_name=_str(Fragment.container_name),
                base_dir=_str(Fragment.base_dir),
            )
        with section(Section.input):
            input_type = _str(Fragment.type)
            input_type = PipelineInputType(input_type) if input_type else None
            storage_type = _str("STORAGE_TYPE")
            storage_type = (
                PipelineInputStorageType(storage_type) if storage_type else None
            )
            input = InputConfigInputModel(
                type=input_type,
                storage_type=storage_type,
                file_encoding=_str(Fragment.encoding),
                base_dir=_str(Fragment.base_dir),
                file_pattern=_str("FILE_PATTERN"),
                source_column=_str("SOURCE_COLUMN"),
                timestamp_column=_str("TIMESTAMP_COLUMN"),
                timestamp_format=_str("TIMESTAMP_FORMAT"),
                text_column=_str("TEXT_COLUMN"),
                title_column=_str("TITLE_COLUMN"),
                document_attribute_columns=_array_string(
                    _str("DOCUMENT_ATTRIBUTE_COLUMNS"),
                ),
            )
        with section(Section.chunk):
            chunks = ChunkingConfigInputModel(
                size=_int("SIZE"),
                overlap=_int("OVERLAP"),
                group_by_columns=_array_string(_str("BY_COLUMNS")),
            )
        with section(Section.snapshot):
            snapshots = SnapshotsConfigInputModel(
                graphml=_bool("GRAPHML"),
                raw_entities=_bool("RAW_ENTITIES"),
                top_level_nodes=_bool("TOP_LEVEL_NODES"),
            )
        with section(Section.entity_extraction):
            entity_extraction = EntityExtractionConfigInputModel(
                entity_types=_array_string(_str("ENTITY_TYPES")),
                max_gleanings=_int(Fragment.max_gleanings),
                prompt=_str(Fragment.prompt_file),
            )
        with section(Section.claim_extraction):
            claim_extraction = ClaimExtractionConfigInputModel(
                description=_str(Fragment.description),
                prompt=_str(Fragment.prompt_file),
                max_gleanings=_int(Fragment.max_gleanings),
            )
        with section(Section.community_report):
            community_reports = CommunityReportsConfigInputModel(
                prompt=_str(Fragment.prompt_file),
                max_length=_int(Fragment.max_length),
                max_input_length=_int("MAX_INPUT_LENGTH"),
            )
        with section(Section.summarize_descriptions):
            summarize_descriptions = SummarizeDescriptionsConfigInputModel(
                prompt=_str(Fragment.prompt_file),
                max_length=_int(Fragment.max_length),
            )
        with section(Section.umap):
            umap = UmapConfigInputModel(
                enabled=_bool(Fragment.enabled),
            )

        async_mode_enum = AsyncType(async_mode) if async_mode else None
        input_model = DefaultConfigParametersInputModel(
            llm=llm_parameters,
            parallelization=llm_parallelization,
            embeddings=text_embeddings,
            embed_graph=embed_graph,
            reporting=reporting,
            storage=storage,
            cache=cache,
            input=input,
            chunks=chunks,
            snapshots=snapshots,
            entity_extraction=entity_extraction,
            claim_extraction=claim_extraction,
            community_reports=community_reports,
            summarize_descriptions=summarize_descriptions,
            umap=umap,
            async_mode=async_mode_enum,
            cluster_graph=ClusterGraphConfigInputModel(
                max_cluster_size=_int("MAX_CLUSTER_SIZE"),
            ),
            encoding_model=_str(Fragment.encoding_model),
            skip_workflows=_array_string(_str("SKIP_WORKFLOWS")),
        )
        return default_config_parameters(input_model, root_dir)


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


def _array_string(
    raw: str | None, default_value: list[str] | None = None
) -> list[str] | None:
    """Filter the array entries."""
    if raw is None:
        return default_value

    result = [r.strip() for r in raw.split(",")]
    return [r for r in result if r != ""]
