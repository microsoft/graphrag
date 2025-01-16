# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""API functions for the GraphRAG module."""

from pathlib import Path
from typing import Any

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.model.types import TextEmbedder
from graphrag.utils.embeddings import create_collection_name
from graphrag.vector_stores.base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)
from graphrag.vector_stores.factory import VectorStoreFactory


class MultiVectorStore(BaseVectorStore):
    """Multi Vector Store wrapper implementation."""

    def __init__(
        self,
        embedding_stores: list[BaseVectorStore],
        index_names: list[str],
    ):
        self.embedding_stores = embedding_stores
        self.index_names = index_names

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into the vector store."""
        msg = "load_documents method not implemented"
        raise NotImplementedError(msg)
    
    def connect(self, **kwargs: Any) -> Any:
        """Connect to vector storage."""
        msg = "connect method not implemented"
        raise NotImplementedError(msg)

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        msg = "filter_by_id method not implemented"
        raise NotImplementedError(msg)
    
    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        msg = "search_by_id method not implemented"
        raise NotImplementedError(msg)

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        all_results = []
        for index_name, embedding_store in zip(self.index_names, self.embedding_stores, strict=False):
            results = embedding_store.similarity_search_by_vector(
                query_embedding=query_embedding, k=k
            )
            mod_results = []
            for r in results:
                r.document.id = str(r.document.id) + f"-{index_name}"
                mod_results += [r]
            all_results += mod_results
        return sorted(all_results, key=lambda x: x.score, reverse=True)[:k]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a text-based similarity search."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(
                query_embedding=query_embedding, k=k
            )
        return []
    
def get_embedding_store(
    config_args: dict | list[dict],
    embedding_name: str,
) -> BaseVectorStore:
    """Get the embedding description store."""
    if isinstance(config_args, dict):
        vector_store_type = config_args["type"]
        collection_name = create_collection_name(
            config_args.get("container_name", "default"), embedding_name
        )
        embedding_store = VectorStoreFactory().create_vector_store(
            vector_store_type=vector_store_type,
            kwargs={**config_args, "collection_name": collection_name},
        )
        embedding_store.connect(**config_args)
        return embedding_store
    config_args_list = config_args
    embedding_stores = []
    index_names = []
    for config_args in config_args_list:
        vector_store_type = config_args["type"]
        collection_name = create_collection_name(
            config_args.get("container_name", "default"), embedding_name
        )
        embedding_store = VectorStoreFactory().create_vector_store(
            vector_store_type=vector_store_type,
            kwargs={**config_args, "collection_name": collection_name},
        )
        embedding_store.connect(**config_args)
        embedding_stores.append(embedding_store)
        index_names.append(config_args["index_name"])
    return MultiVectorStore(embedding_stores, index_names)

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

def update_context_data(
    context_data: Any,
    links: dict[str, Any],
) -> Any:
    """
    Update context data with lthe links dict so that it contains both the index name and community id.

    Parameters
    ----------
    - context_data (str | list[pd.DataFrame] | dict[str, pd.DataFrame]): The context data to update.
    - links (dict[str, Any]): A dictionary of links to the original dataframes.

    Returns
    -------
    str | list[pd.DataFrame] | dict[str, pd.DataFrame]: The updated context data.
    """
    updated_context_data = {}
    for key in context_data:
        updated_entry = []
        if key == "reports":
            updated_entry = [
                dict(
                    {k: entry[k] for k in entry},
                    index_name=links["community_reports"][int(entry["id"])][
                            "index_name"
                        ], index_id=links["community_reports"][int(entry["id"])]["id"],
                )
                for entry in context_data[key]
            ]
        if key == "entities":
            updated_entry = [
                dict(
                    {k: entry[k] for k in entry},
                    entity=entry["entity"].split("-")[0], index_name=links["entities"][int(entry["id"])]["index_name"], index_id=links["entities"][int(entry["id"])]["id"],
                )
                for entry in context_data[key]
            ]
        if key == "relationships":
            updated_entry = [
                dict(
                    {k: entry[k] for k in entry},
                    source=entry["source"].split("-")[0], target=entry["target"].split("-")[0], index_name=links["relationships"][int(entry["id"])][
                            "index_name"
                        ], index_id=links["relationships"][int(entry["id"])]["id"],
                )
                for entry in context_data[key]
            ]
        if key == "claims":
            updated_entry = [
                dict(
                    {k: entry[k] for k in entry},
                    index_name=links["claims"][int(entry["id"])]["index_name"], index_id=links["claims"][int(entry["id"])]["id"],
                )
                for entry in context_data[key]
            ]
        if key == "sources":
            updated_entry = [
                dict(
                    {k: entry[k] for k in entry},
                    index_name=links["text_units"][int(entry["id"])]["index_name"], index_id=links["text_units"][int(entry["id"])]["id"],
                )
                for entry in context_data[key]
            ]
        updated_context_data[key] = updated_entry
    return updated_context_data

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

def get_workflows_list(config: GraphRagConfig) -> list[str]:
    """Return a list of workflows for the indexing pipeline."""
    return [
        "create_base_text_units",
        "create_final_documents",
        "extract_graph",
        "compute_communities",
        "create_final_entities",
        "create_final_relationships",
        "create_final_nodes",
        "create_final_communities",
        *(["create_final_covariates"] if config.claim_extraction.enabled else []),
        "create_final_text_units",
        "create_final_community_reports",
        "generate_text_embeddings",
    ]
