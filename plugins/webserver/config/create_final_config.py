import logging
import os

log = logging.getLogger(__name__)
from pathlib import Path
from typing import cast

from datashaper import AsyncType
from dotenv import dotenv_values
from environs import Env

import graphrag.config.defaults as defs
from graphrag.config.create_graphrag_config import _token_replace, Section, Fragment, _is_azure

from graphrag.config.enums import (
    CacheType,
    InputFileType,
    InputType,
    LLMType,
    ReportingType,
    StorageType,
    TextEmbeddingTarget,
)
from graphrag.config.environment_reader import EnvironmentReader
from graphrag.config.errors import (
    ApiKeyMissingError,
    AzureApiBaseMissingError,
    AzureDeploymentNameMissingError,
)
from graphrag.config.input_models import (
    LLMConfigInput,
)
from graphrag.config.models import (
    CacheConfig,
    ChunkingConfig,
    ClaimExtractionConfig,
    ClusterGraphConfig,
    CommunityReportsConfig,
    EmbedGraphConfig,
    EntityExtractionConfig,
    GlobalSearchConfig,
    GraphRagConfig,
    InputConfig,
    LLMParameters,
    LocalSearchConfig,
    ParallelizationParameters,
    ReportingConfig,
    SnapshotsConfig,
    StorageConfig,
    SummarizeDescriptionsConfig,
    TextEmbeddingConfig,
    UmapConfig,
)
from plugins.webserver.config.final_config import FinalConfig
from plugins.webserver.config.query_config import QueryConfig
from plugins.webserver.config import defaults as webserver_defaults


def create_final_config(
        values: dict | None = None, root_dir: str | None = None, domain_config: GraphRagConfig = None
) -> FinalConfig:
    """Load Configuration Parameters from a dictionary."""
    values = values or {}
    root_dir = root_dir or str(Path.cwd())
    env = _make_env(root_dir)
    _token_replace(cast(dict, values))

    reader = EnvironmentReader(env)

    def hydrate_async_type(input: LLMConfigInput, base: AsyncType) -> AsyncType:
        value = input.get(Fragment.async_mode)
        return AsyncType(value) if value else base

    def hydrate_llm_params(
            config: LLMConfigInput, base: LLMParameters
    ) -> LLMParameters:
        with reader.use(config.get("llm")):
            llm_type = reader.str(Fragment.type)
            llm_type = LLMType(llm_type) if llm_type else base.type
            api_key = reader.str(Fragment.api_key) or base.api_key
            api_base = reader.str(Fragment.api_base) or base.api_base
            cognitive_services_endpoint = (
                    reader.str(Fragment.cognitive_services_endpoint)
                    or base.cognitive_services_endpoint
            )
            deployment_name = (
                    reader.str(Fragment.deployment_name) or base.deployment_name
            )

            if api_key is None and not _is_azure(llm_type):
                raise ApiKeyMissingError
            if _is_azure(llm_type):
                if api_base is None:
                    raise AzureApiBaseMissingError
                if deployment_name is None:
                    raise AzureDeploymentNameMissingError

            sleep_on_rate_limit = reader.bool(Fragment.sleep_recommendation)
            if sleep_on_rate_limit is None:
                sleep_on_rate_limit = base.sleep_on_rate_limit_recommendation

            return LLMParameters(
                api_key=api_key,
                type=llm_type,
                api_base=api_base,
                api_version=reader.str(Fragment.api_version) or base.api_version,
                organization=reader.str("organization") or base.organization,
                proxy=reader.str("proxy") or base.proxy,
                model=reader.str("model") or base.model,
                max_tokens=reader.int(Fragment.max_tokens) or base.max_tokens,
                temperature=reader.float(Fragment.temperature) or base.temperature,
                top_p=reader.float(Fragment.top_p) or base.top_p,
                n=reader.int(Fragment.n) or base.n,
                model_supports_json=reader.bool(Fragment.model_supports_json)
                                    or base.model_supports_json,
                request_timeout=reader.float(Fragment.request_timeout)
                                or base.request_timeout,
                cognitive_services_endpoint=cognitive_services_endpoint,
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
            config: LLMConfigInput, base: LLMParameters
    ) -> LLMParameters:
        with reader.use(config.get("llm")):
            api_type = reader.str(Fragment.type) or defs.EMBEDDING_TYPE
            api_type = LLMType(api_type) if api_type else defs.LLM_TYPE
            api_key = reader.str(Fragment.api_key) or base.api_key

            # In a unique events where:
            # - same api_bases for LLM and embeddings (both Azure)
            # - different api_bases for LLM and embeddings (both Azure)
            # - LLM uses Azure OpenAI, while embeddings uses base OpenAI (this one is important)
            # - LLM uses Azure OpenAI, while embeddings uses third-party OpenAI-like API
            api_base = (
                reader.str(Fragment.api_base) or base.api_base
                if _is_azure(api_type)
                else reader.str(Fragment.api_base)
            )
            api_version = (
                reader.str(Fragment.api_version) or base.api_version
                if _is_azure(api_type)
                else reader.str(Fragment.api_version)
            )
            api_organization = reader.str("organization") or base.organization
            api_proxy = reader.str("proxy") or base.proxy
            cognitive_services_endpoint = (
                    reader.str(Fragment.cognitive_services_endpoint)
                    or base.cognitive_services_endpoint
            )
            deployment_name = reader.str(Fragment.deployment_name)

            if api_key is None and not _is_azure(api_type):
                raise ApiKeyMissingError(embedding=True)
            if _is_azure(api_type):
                if api_base is None:
                    raise AzureApiBaseMissingError(embedding=True)
                if deployment_name is None:
                    raise AzureDeploymentNameMissingError(embedding=True)

            sleep_on_rate_limit = reader.bool(Fragment.sleep_recommendation)
            if sleep_on_rate_limit is None:
                sleep_on_rate_limit = base.sleep_on_rate_limit_recommendation

            return LLMParameters(
                api_key=api_key,
                type=api_type,
                api_base=api_base,
                api_version=api_version,
                organization=api_organization,
                proxy=api_proxy,
                model=reader.str(Fragment.model) or defs.EMBEDDING_MODEL,
                request_timeout=reader.float(Fragment.request_timeout)
                                or defs.LLM_REQUEST_TIMEOUT,
                cognitive_services_endpoint=cognitive_services_endpoint,
                deployment_name=deployment_name,
                tokens_per_minute=reader.int("tokens_per_minute", Fragment.tpm)
                                  or defs.LLM_TOKENS_PER_MINUTE,
                requests_per_minute=reader.int("requests_per_minute", Fragment.rpm)
                                    or defs.LLM_REQUESTS_PER_MINUTE,
                max_retries=reader.int(Fragment.max_retries) or defs.LLM_MAX_RETRIES,
                max_retry_wait=reader.float(Fragment.max_retry_wait)
                               or defs.LLM_MAX_RETRY_WAIT,
                sleep_on_rate_limit_recommendation=sleep_on_rate_limit,
                concurrent_requests=reader.int(Fragment.concurrent_requests)
                                    or defs.LLM_CONCURRENT_REQUESTS,
            )

    def hydrate_parallelization_params(
            config: LLMConfigInput, base: ParallelizationParameters
    ) -> ParallelizationParameters:
        with reader.use(config.get("parallelization")):
            return ParallelizationParameters(
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
        async_mode = AsyncType(async_mode) if async_mode else defs.ASYNC_MODE

        fallback_oai_key = reader.str(Fragment.api_key) or fallback_oai_key
        fallback_oai_org = reader.str(Fragment.api_organization) or fallback_oai_org
        fallback_oai_base = reader.str(Fragment.api_base) or fallback_oai_base
        fallback_oai_version = reader.str(Fragment.api_version) or fallback_oai_version
        fallback_oai_proxy = reader.str(Fragment.api_proxy)

        with reader.envvar_prefix(Section.llm):
            with reader.use(values.get("llm")):
                llm_type = reader.str(Fragment.type)
                llm_type = LLMType(llm_type) if llm_type else defs.LLM_TYPE
                api_key = reader.str(Fragment.api_key) or fallback_oai_key
                api_organization = (
                        reader.str(Fragment.api_organization) or fallback_oai_org
                )
                api_base = reader.str(Fragment.api_base) or fallback_oai_base
                api_version = reader.str(Fragment.api_version) or fallback_oai_version
                api_proxy = reader.str(Fragment.api_proxy) or fallback_oai_proxy
                cognitive_services_endpoint = reader.str(
                    Fragment.cognitive_services_endpoint
                )
                deployment_name = reader.str(Fragment.deployment_name)

                if api_key is None and not _is_azure(llm_type):
                    raise ApiKeyMissingError
                if _is_azure(llm_type):
                    if api_base is None:
                        raise AzureApiBaseMissingError
                    if deployment_name is None:
                        raise AzureDeploymentNameMissingError

                sleep_on_rate_limit = reader.bool(Fragment.sleep_recommendation)
                if sleep_on_rate_limit is None:
                    sleep_on_rate_limit = defs.LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION

                llm_model = LLMParameters(
                    api_key=api_key,
                    api_base=api_base,
                    api_version=api_version,
                    organization=api_organization,
                    proxy=api_proxy,
                    type=llm_type,
                    model=reader.str(Fragment.model) or defs.LLM_MODEL,
                    max_tokens=reader.int(Fragment.max_tokens) or defs.LLM_MAX_TOKENS,
                    temperature=reader.float(Fragment.temperature)
                                or defs.LLM_TEMPERATURE,
                    top_p=reader.float(Fragment.top_p) or defs.LLM_TOP_P,
                    n=reader.int(Fragment.n) or defs.LLM_N,
                    model_supports_json=reader.bool(Fragment.model_supports_json),
                    request_timeout=reader.float(Fragment.request_timeout)
                                    or defs.LLM_REQUEST_TIMEOUT,
                    cognitive_services_endpoint=cognitive_services_endpoint,
                    deployment_name=deployment_name,
                    tokens_per_minute=reader.int(Fragment.tpm)
                                      or defs.LLM_TOKENS_PER_MINUTE,
                    requests_per_minute=reader.int(Fragment.rpm)
                                        or defs.LLM_REQUESTS_PER_MINUTE,
                    max_retries=reader.int(Fragment.max_retries)
                                or defs.LLM_MAX_RETRIES,
                    max_retry_wait=reader.float(Fragment.max_retry_wait)
                                   or defs.LLM_MAX_RETRY_WAIT,
                    sleep_on_rate_limit_recommendation=sleep_on_rate_limit,
                    concurrent_requests=reader.int(Fragment.concurrent_requests)
                                        or defs.LLM_CONCURRENT_REQUESTS,
                )
            with reader.use(values.get("parallelization")):
                llm_parallelization_model = ParallelizationParameters(
                    stagger=reader.float("stagger", Fragment.thread_stagger)
                            or defs.PARALLELIZATION_STAGGER,
                    num_threads=reader.int("num_threads", Fragment.thread_count)
                                or defs.PARALLELIZATION_NUM_THREADS,
                )
        embeddings_config = values.get("embeddings") or {}
        with reader.envvar_prefix(Section.embedding), reader.use(embeddings_config):
            embeddings_target = reader.str("target")
            embeddings_model = TextEmbeddingConfig(
                llm=hydrate_embeddings_params(embeddings_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    embeddings_config, llm_parallelization_model
                ),
                vector_store=embeddings_config.get("vector_store", None),
                async_mode=hydrate_async_type(embeddings_config, async_mode),
                target=(
                    TextEmbeddingTarget(embeddings_target)
                    if embeddings_target
                    else defs.EMBEDDING_TARGET
                ),
                batch_size=reader.int("batch_size") or defs.EMBEDDING_BATCH_SIZE,
                batch_max_tokens=reader.int("batch_max_tokens")
                                 or defs.EMBEDDING_BATCH_MAX_TOKENS,
                skip=reader.list("skip") or [],
            )
        with (
            reader.envvar_prefix(Section.node2vec),
            reader.use(values.get("embed_graph")),
        ):
            embed_graph_model = EmbedGraphConfig(
                enabled=reader.bool(Fragment.enabled) or defs.NODE2VEC_ENABLED,
                num_walks=reader.int("num_walks") or defs.NODE2VEC_NUM_WALKS,
                walk_length=reader.int("walk_length") or defs.NODE2VEC_WALK_LENGTH,
                window_size=reader.int("window_size") or defs.NODE2VEC_WINDOW_SIZE,
                iterations=reader.int("iterations") or defs.NODE2VEC_ITERATIONS,
                random_seed=reader.int("random_seed") or defs.NODE2VEC_RANDOM_SEED,
            )
        with reader.envvar_prefix(Section.input), reader.use(values.get("input")):
            input_type = reader.str("type")
            file_type = reader.str(Fragment.file_type)
            input_model = InputConfig(
                file_type=(
                    InputFileType(file_type) if file_type else defs.INPUT_FILE_TYPE
                ),
                type=(InputType(input_type) if input_type else defs.INPUT_TYPE),
                encoding=reader.str("file_encoding", Fragment.encoding)
                         or defs.INPUT_FILE_ENCODING,
                base_dir=reader.str(Fragment.base_dir) or defs.INPUT_BASE_DIR,
                file_pattern=reader.str("file_pattern")
                             or (
                                 defs.INPUT_TEXT_PATTERN
                                 if file_type == InputFileType.text
                                 else defs.INPUT_CSV_PATTERN
                             ),
                source_column=reader.str("source_column"),
                timestamp_column=reader.str("timestamp_column"),
                timestamp_format=reader.str("timestamp_format"),
                text_column=reader.str("text_column") or defs.INPUT_TEXT_COLUMN,
                title_column=reader.str("title_column"),
                document_attribute_columns=reader.list("document_attribute_columns")
                                           or [],
                connection_string=reader.str(Fragment.conn_string),
                storage_account_blob_url=reader.str(Fragment.storage_account_blob_url),
                container_name=reader.str(Fragment.container_name),
            )
        with reader.envvar_prefix(Section.cache), reader.use(values.get("cache")):
            c_type = reader.str(Fragment.type)
            cache_model = CacheConfig(
                type=CacheType(c_type) if c_type else defs.CACHE_TYPE,
                connection_string=reader.str(Fragment.conn_string),
                storage_account_blob_url=reader.str(Fragment.storage_account_blob_url),
                container_name=reader.str(Fragment.container_name),
                base_dir=reader.str(Fragment.base_dir) or defs.CACHE_BASE_DIR,
            )
        with (
            reader.envvar_prefix(Section.reporting),
            reader.use(values.get("reporting")),
        ):
            r_type = reader.str(Fragment.type)
            reporting_model = ReportingConfig(
                type=ReportingType(r_type) if r_type else defs.REPORTING_TYPE,
                connection_string=reader.str(Fragment.conn_string),
                storage_account_blob_url=reader.str(Fragment.storage_account_blob_url),
                container_name=reader.str(Fragment.container_name),
                base_dir=reader.str(Fragment.base_dir) or defs.REPORTING_BASE_DIR,
            )
        with reader.envvar_prefix(Section.storage), reader.use(values.get("storage")):
            s_type = reader.str(Fragment.type)
            storage_model = StorageConfig(
                type=StorageType(s_type) if s_type else defs.STORAGE_TYPE,
                connection_string=reader.str(Fragment.conn_string),
                storage_account_blob_url=reader.str(Fragment.storage_account_blob_url),
                container_name=reader.str(Fragment.container_name),
                base_dir=reader.str(Fragment.base_dir) or defs.STORAGE_BASE_DIR,
            )
        with reader.envvar_prefix(Section.chunk), reader.use(values.get("chunks")):
            group_by_columns = reader.list("group_by_columns", "BY_COLUMNS")
            if group_by_columns is None:
                group_by_columns = defs.CHUNK_GROUP_BY_COLUMNS

            chunks_model = ChunkingConfig(
                size=reader.int("size") or defs.CHUNK_SIZE,
                overlap=reader.int("overlap") or defs.CHUNK_OVERLAP,
                group_by_columns=group_by_columns,
                encoding_model=reader.str(Fragment.encoding_model),
            )
        with (
            reader.envvar_prefix(Section.snapshot),
            reader.use(values.get("snapshots")),
        ):
            snapshots_model = SnapshotsConfig(
                graphml=reader.bool("graphml") or defs.SNAPSHOTS_GRAPHML,
                raw_entities=reader.bool("raw_entities") or defs.SNAPSHOTS_RAW_ENTITIES,
                top_level_nodes=reader.bool("top_level_nodes")
                                or defs.SNAPSHOTS_TOP_LEVEL_NODES,
            )
        with reader.envvar_prefix(Section.umap), reader.use(values.get("umap")):
            umap_model = UmapConfig(
                enabled=reader.bool(Fragment.enabled) or defs.UMAP_ENABLED,
            )

        entity_extraction_config = values.get("entity_extraction") or {}
        with (
            reader.envvar_prefix(Section.entity_extraction),
            reader.use(entity_extraction_config),
        ):
            max_gleanings = reader.int(Fragment.max_gleanings)
            max_gleanings = (
                max_gleanings
                if max_gleanings is not None
                else defs.ENTITY_EXTRACTION_MAX_GLEANINGS
            )

            entity_extraction_model = EntityExtractionConfig(
                llm=hydrate_llm_params(entity_extraction_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    entity_extraction_config, llm_parallelization_model
                ),
                async_mode=hydrate_async_type(entity_extraction_config, async_mode),
                entity_types=reader.list("entity_types")
                             or defs.ENTITY_EXTRACTION_ENTITY_TYPES,
                max_gleanings=max_gleanings,
                prompt=reader.str("prompt", Fragment.prompt_file),
                encoding_model=reader.str(Fragment.encoding_model),
            )

        claim_extraction_config = values.get("claim_extraction") or {}
        with (
            reader.envvar_prefix(Section.claim_extraction),
            reader.use(claim_extraction_config),
        ):
            max_gleanings = reader.int(Fragment.max_gleanings)
            max_gleanings = (
                max_gleanings if max_gleanings is not None else defs.CLAIM_MAX_GLEANINGS
            )
            claim_extraction_model = ClaimExtractionConfig(
                enabled=reader.bool(Fragment.enabled) or defs.CLAIM_EXTRACTION_ENABLED,
                llm=hydrate_llm_params(claim_extraction_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    claim_extraction_config, llm_parallelization_model
                ),
                async_mode=hydrate_async_type(claim_extraction_config, async_mode),
                description=reader.str("description") or defs.CLAIM_DESCRIPTION,
                prompt=reader.str("prompt", Fragment.prompt_file),
                max_gleanings=max_gleanings,
                encoding_model=reader.str(Fragment.encoding_model),
            )

        community_report_config = values.get("community_reports") or {}
        with (
            reader.envvar_prefix(Section.community_reports),
            reader.use(community_report_config),
        ):
            community_reports_model = CommunityReportsConfig(
                llm=hydrate_llm_params(community_report_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    community_report_config, llm_parallelization_model
                ),
                async_mode=hydrate_async_type(community_report_config, async_mode),
                prompt=reader.str("prompt", Fragment.prompt_file),
                max_length=reader.int(Fragment.max_length)
                           or defs.COMMUNITY_REPORT_MAX_LENGTH,
                max_input_length=reader.int("max_input_length")
                                 or defs.COMMUNITY_REPORT_MAX_INPUT_LENGTH,
            )

        summarize_description_config = values.get("summarize_descriptions") or {}
        with (
            reader.envvar_prefix(Section.summarize_descriptions),
            reader.use(values.get("summarize_descriptions")),
        ):
            summarize_descriptions_model = SummarizeDescriptionsConfig(
                llm=hydrate_llm_params(summarize_description_config, llm_model),
                parallelization=hydrate_parallelization_params(
                    summarize_description_config, llm_parallelization_model
                ),
                async_mode=hydrate_async_type(summarize_description_config, async_mode),
                prompt=reader.str("prompt", Fragment.prompt_file),
                max_length=reader.int(Fragment.max_length)
                           or defs.SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
            )

        with reader.use(values.get("cluster_graph")):
            cluster_graph_model = ClusterGraphConfig(
                max_cluster_size=reader.int("max_cluster_size") or defs.MAX_CLUSTER_SIZE
            )

        with (
            reader.use(values.get("local_search")),
            reader.envvar_prefix(Section.local_search),
        ):
            local_search_model = LocalSearchConfig(
                text_unit_prop=reader.float("text_unit_prop")
                               or defs.LOCAL_SEARCH_TEXT_UNIT_PROP,
                community_prop=reader.float("community_prop")
                               or defs.LOCAL_SEARCH_COMMUNITY_PROP,
                conversation_history_max_turns=reader.int(
                    "conversation_history_max_turns"
                )
                                               or defs.LOCAL_SEARCH_CONVERSATION_HISTORY_MAX_TURNS,
                top_k_entities=reader.int("top_k_entities")
                               or defs.LOCAL_SEARCH_TOP_K_MAPPED_ENTITIES,
                top_k_relationships=reader.int("top_k_relationships")
                                    or defs.LOCAL_SEARCH_TOP_K_RELATIONSHIPS,
                temperature=reader.float("llm_temperature")
                            or defs.LOCAL_SEARCH_LLM_TEMPERATURE,
                top_p=reader.float("llm_top_p") or defs.LOCAL_SEARCH_LLM_TOP_P,
                n=reader.int("llm_n") or defs.LOCAL_SEARCH_LLM_N,
                max_tokens=reader.int(Fragment.max_tokens)
                           or defs.LOCAL_SEARCH_MAX_TOKENS,
                llm_max_tokens=reader.int("llm_max_tokens")
                               or defs.LOCAL_SEARCH_LLM_MAX_TOKENS,
            )

        with (
            reader.use(values.get("global_search")),
            reader.envvar_prefix(Section.global_search),
        ):
            global_search_model = GlobalSearchConfig(
                temperature=reader.float("llm_temperature")
                            or defs.GLOBAL_SEARCH_LLM_TEMPERATURE,
                top_p=reader.float("llm_top_p") or defs.GLOBAL_SEARCH_LLM_TOP_P,
                n=reader.int("llm_n") or defs.GLOBAL_SEARCH_LLM_N,
                max_tokens=reader.int(Fragment.max_tokens)
                           or defs.GLOBAL_SEARCH_MAX_TOKENS,
                data_max_tokens=reader.int("data_max_tokens")
                                or defs.GLOBAL_SEARCH_DATA_MAX_TOKENS,
                map_max_tokens=reader.int("map_max_tokens")
                               or defs.GLOBAL_SEARCH_MAP_MAX_TOKENS,
                reduce_max_tokens=reader.int("reduce_max_tokens")
                                  or defs.GLOBAL_SEARCH_REDUCE_MAX_TOKENS,
                concurrency=reader.int("concurrency") or defs.GLOBAL_SEARCH_CONCURRENCY,
            )

        with (
            reader.use(values.get("query")),
        ):
            query = QueryConfig(
                community_level=reader.int("community_level") or webserver_defaults.QUERY_COMMUNITY_LEVEL,
                response_type=reader.str("response_type") or webserver_defaults.QUERY_RESPONSE_TYPE
            )

        encoding_model = reader.str(Fragment.encoding_model) or defs.ENCODING_MODEL
        skip_workflows = reader.list("skip_workflows") or []

        all_index_dir = reader.str("all_index_dir")

    return FinalConfig(
        query=query,
        all_index_dir=all_index_dir,
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
        local_search=local_search_model,
        global_search=global_search_model,
    )


def _make_env(root_dir: str) -> Env:
    env_path = Path(root_dir) / ".env"
    if env_path.exists():
        log.info("Loading pipeline .env file")
        env_config = dotenv_values(f"{env_path}")
        for key, value in env_config.items():
            os.environ[key] = value or ""
    else:
        log.info("No .env file found at %s", root_dir)
    env = Env(expand_vars=True)
    env.read_env()
    return env