# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Common default configuration values."""

from graphrag.index.config import (
    PipelineCacheType,
    PipelineInputStorageType,
    PipelineInputType,
    PipelineReportingType,
    PipelineStorageType,
)
from graphrag.index.default_config.parameters.models import TextEmbeddingTarget

#
# LLM Parameters
#
DEFAULT_LLM_TYPE = "openai_chat"
DEFAULT_LLM_MODEL = "gpt-4-turbo-preview"
DEFAULT_LLM_MAX_TOKENS = 4000
DEFAULT_LLM_REQUEST_TIMEOUT = 180.0
DEFAULT_LLM_TOKENS_PER_MINUTE = 0
DEFAULT_LLM_REQUESTS_PER_MINUTE = 0
DEFAULT_LLM_MAX_RETRIES = 10
DEFAULT_LLM_MAX_RETRY_WAIT = 10.0
DEFAULT_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION = True
DEFAULT_LLM_CONCURRENT_REQUESTS = 25

#
# Text Embedding Parameters
#
DEFAULT_EMBEDDING_TYPE = "openai_embedding"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_TOKENS_PER_MINUTE = 0
DEFAULT_EMBEDDING_REQUESTS_PER_MINUTE = 0
DEFAULT_EMBEDDING_MAX_RETRIES = 10
DEFAULT_EMBEDDING_MAX_RETRY_WAIT = 10.0
DEFAULT_EMBEDDING_SLEEP_ON_RATE_LIMIT_RECOMMENDATION = True
DEFAULT_EMBEDDING_CONCURRENT_REQUESTS = 25
DEFAULT_EMBEDDING_BATCH_SIZE = 16
DEFAULT_EMBEDDING_BATCH_MAX_TOKENS = 8191
DEFAULT_EMBEDDING_TARGET = TextEmbeddingTarget.required

DEFAULT_CACHE_TYPE = PipelineCacheType.file
DEFAULT_CACHE_BASE_DIR = "cache"
DEFAULT_CHUNK_SIZE = 300
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_CHUNK_GROUP_BY_COLUMNS = ["id"]
DEFAULT_CLAIM_DESCRIPTION = (
    "Any claims or facts that could be relevant to information discovery."
)
DEFAULT_CLAIM_MAX_GLEANINGS = 0
DEFAULT_MAX_CLUSTER_SIZE = 10
DEFAULT_COMMUNITY_REPORT_MAX_LENGTH = 1500
DEFAULT_COMMUNITY_REPORT_MAX_INPUT_LENGTH = 12_000
DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES = ["organization", "person", "geo", "event"]
DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS = 0
DEFAULT_INPUT_TYPE = PipelineInputType.csv
DEFAULT_INPUT_STORAGE_TYPE = PipelineInputStorageType.file
DEFAULT_INPUT_BASE_DIR = ""
DEFAULT_INPUT_FILE_ENCODING = "utf-8"
DEFAULT_INPUT_TEXT_COLUMN = "text"
DEFAULT_INPUT_CSV_PATTERN = ".*\\.csv$"
DEFAULT_INPUT_TEXT_PATTERN = ".*\\.txt$"
DEFAULT_PARALLELIZATION_STAGGER = 0.3
DEFAULT_PARALLELIZATION_NUM_THREADS = 50
DEFAULT_NODE2VEC_IS_ENABLED = False
DEFAULT_NODE2VEC_NUM_WALKS = 10
DEFAULT_NODE2VEC_WALK_LENGTH = 40
DEFAULT_NODE2VEC_WINDOW_SIZE = 2
DEFAULT_NODE2VEC_ITERATIONS = 3
DEFAULT_NODE2VEC_RANDOM_SEED = 597832
DEFAULT_REPORTING_TYPE = PipelineReportingType.file
DEFAULT_REPORTING_BASE_DIR = "output/${timestamp}/reports"
DEFAULT_SNAPSHOTS_GRAPHML = False
DEFAULT_SNAPSHOTS_RAW_ENTITIES = False
DEFAULT_SNAPSHOTS_TOP_LEVEL_NODES = False
DEFAULT_STORAGE_TYPE = PipelineStorageType.file
DEFAULT_STORAGE_BASE_DIR = "output/${timestamp}/artifacts"
DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH = 500
DEFAULT_UMAP_ENABLED = False
