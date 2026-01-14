# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""API functions for the GraphRAG module."""

from pathlib import Path

from graphrag_vectors import (
    VectorStore,
    VectorStoreConfig,
    create_vector_store,
)


def get_embedding_store(
    config: VectorStoreConfig,
    embedding_name: str,
) -> VectorStore:
    """Get the embedding store."""
    embedding_store = create_vector_store(config, config.index_schema[embedding_name])
    embedding_store.connect()

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


def load_search_prompt(prompt_config: str | None) -> str | None:
    """
    Load the search prompt from disk if configured.

    If not, leave it empty - the search functions will load their defaults.

    """
    if prompt_config:
        prompt_file = Path(prompt_config).resolve()
        if prompt_file.exists():
            return prompt_file.read_bytes().decode(encoding="utf-8")
    return None


def truncate(text: str, max_length: int) -> str:
    """Truncate a string to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "...[truncated]"
