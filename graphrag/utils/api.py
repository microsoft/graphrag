# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""API functions for the GraphRAG module."""

from pathlib import Path
from typing import Any

from graphrag.cache.factory import CacheFactory
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.embeddings import create_index_name
from graphrag.config.models.cache_config import CacheConfig
from graphrag.config.models.storage_config import StorageConfig
from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig
from graphrag.storage.factory import StorageFactory
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.vector_stores.base import (
    BaseVectorStore,
)
from graphrag.vector_stores.factory import VectorStoreFactory


def get_embedding_store(
    store: dict[str, Any],
    embedding_name: str,
) -> BaseVectorStore:
    """Get the embedding description store."""
    vector_store_type = store["type"]
    index_name = create_index_name(
        store.get("container_name", "default"), embedding_name
    )

    embeddings_schema: dict[str, VectorStoreSchemaConfig] = store.get(
        "embeddings_schema", {}
    )
    embedding_config: VectorStoreSchemaConfig = VectorStoreSchemaConfig()

    if (
        embeddings_schema is not None
        and embedding_name is not None
        and embedding_name in embeddings_schema
    ):
        raw_config = embeddings_schema[embedding_name]
        if isinstance(raw_config, dict):
            embedding_config = VectorStoreSchemaConfig(**raw_config)
        else:
            embedding_config = raw_config

    if embedding_config.index_name is None:
        embedding_config.index_name = index_name

    embedding_store = VectorStoreFactory().create_vector_store(
        vector_store_type=vector_store_type,
        vector_store_schema_config=embedding_config,
        **store,
    )
    embedding_store.connect(**store)

    return embedding_store


def reformat_context_data(context_data: dict) -> dict:
    """
    Reformats context_data for all query responses.

    Reformats a dictionary of dataframes into a dictionary of lists.
    One list entry for each record. Records are grouped by original
    dictionary keys.

    Note: depending on which query algorithm is used, the context_data may not
          contain the same information (keys). In this case, the default behavior will be to
          set these keys as empty lists to preserve a standard output format.
    """
    final_format = {
        "reports": [],
        "entities": [],
        "relationships": [],
        "claims": [],
        "sources": [],
    }
    for key in context_data:
        records = (
            context_data[key].to_dict(orient="records")
            if context_data[key] is not None and not isinstance(context_data[key], dict)
            else context_data[key]
        )
        if len(records) < 1:
            continue
        final_format[key] = records
    return final_format


def load_search_prompt(root_dir: str, prompt_config: str | None) -> str | None:
    """
    Load the search prompt from disk if configured.

    If not, leave it empty - the search functions will load their defaults.

    """
    if prompt_config:
        prompt_file = Path(root_dir) / prompt_config
        if prompt_file.exists():
            return prompt_file.read_bytes().decode(encoding="utf-8")
    return None


def create_storage_from_config(output: StorageConfig) -> PipelineStorage:
    """Create a storage object from the config."""
    storage_config = output.model_dump()
    return StorageFactory().create_storage(
        storage_type=storage_config["type"],
        kwargs=storage_config,
    )


def create_cache_from_config(cache: CacheConfig, root_dir: str) -> PipelineCache:
    """Create a cache object from the config."""
    cache_config = cache.model_dump()
    kwargs = {**cache_config, "root_dir": root_dir}
    return CacheFactory().create_cache(
        cache_type=cache_config["type"],
        kwargs=kwargs,
    )


def truncate(text: str, max_length: int) -> str:
    """Truncate a string to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "...[truncated]"
