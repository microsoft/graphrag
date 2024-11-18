# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the Azure AI Search  vector store implementation."""

import json
from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from graphrag.model.types import TextEmbedder
from graphrag.vector_stores.base import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class AzureAISearch(BaseVectorStore):
    """Azure AI Search vector storage implementation."""

    index_client: SearchIndexClient

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def connect(self, **kwargs: Any) -> Any:
        """Connect to AI search vector storage."""
        url = kwargs["url"]
        api_key = kwargs.get("api_key")
        audience = kwargs.get("audience")
        self.vector_size = kwargs.get("vector_size", DEFAULT_VECTOR_SIZE)

        self.vector_search_profile_name = kwargs.get(
            "vector_search_profile_name", "vectorSearchProfile"
        )

        if url:
            audience_arg = {"audience": audience} if audience and not api_key else {}
            self.db_connection = SearchClient(
                endpoint=url,
                index_name=self.collection_name,
                credential=(
                    AzureKeyCredential(api_key) if api_key else DefaultAzureCredential()
                ),
                **audience_arg,
            )
            self.index_client = SearchIndexClient(
                endpoint=url,
                credential=(
                    AzureKeyCredential(api_key) if api_key else DefaultAzureCredential()
                ),
                **audience_arg,
            )
        else:
            not_supported_error = "Azure AI Search expects `url`."
            raise ValueError(not_supported_error)

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into an Azure AI Search index."""
        if overwrite:
            if self.collection_name in self.index_client.list_index_names():
                self.index_client.delete_index(self.collection_name)

            # Configure vector search profile
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="HnswAlg",
                        parameters=HnswParameters(
                            metric=VectorSearchAlgorithmMetric.COSINE
                        ),
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name=self.vector_search_profile_name,
                        algorithm_configuration_name="HnswAlg",
                    )
                ],
            )
            # Configure the index
            index = SearchIndex(
                name=self.collection_name,
                fields=[
                    SimpleField(
                        name="id",
                        type=SearchFieldDataType.String,
                        key=True,
                    ),
                    SearchField(
                        name="vector",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True,
                        vector_search_dimensions=self.vector_size,
                        vector_search_profile_name=self.vector_search_profile_name,
                    ),
                    SearchableField(name="text", type=SearchFieldDataType.String),
                    SimpleField(
                        name="attributes",
                        type=SearchFieldDataType.String,
                    ),
                ],
                vector_search=vector_search,
            )
            self.index_client.create_or_update_index(
                index,
            )

        batch = [
            {
                "id": doc.id,
                "vector": doc.vector,
                "text": doc.text,
                "attributes": json.dumps(doc.attributes),
            }
            for doc in documents
            if doc.vector is not None
        ]

        if len(batch) > 0:
            self.db_connection.upload_documents(batch)

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by a list of ids."""
        if include_ids is None or len(include_ids) == 0:
            self.query_filter = None
            # Returning to keep consistency with other methods, but not needed
            return self.query_filter

        # More info about odata filtering here: https://learn.microsoft.com/en-us/azure/search/search-query-odata-search-in-function
        # search.in is faster that joined and/or conditions
        id_filter = ",".join([f"{id!s}" for id in include_ids])
        self.query_filter = f"search.in(id, '{id_filter}', ',')"

        # Returning to keep consistency with other methods, but not needed
        # TODO: Refactor on a future PR
        return self.query_filter

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        vectorized_query = VectorizedQuery(
            vector=query_embedding, k_nearest_neighbors=k, fields="vector"
        )

        response = self.db_connection.search(
            vector_queries=[vectorized_query],
        )

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc.get("id", ""),
                    text=doc.get("text", ""),
                    vector=doc.get("vector", []),
                    attributes=(json.loads(doc.get("attributes", "{}"))),
                ),
                # Cosine similarity between 0.333 and 1.000
                # https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking#scores-in-a-hybrid-search-results
                score=doc["@search.score"],
            )
            for doc in response
        ]

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

    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        response = self.db_connection.get_document(id)
        return VectorStoreDocument(
            id=response.get("id", ""),
            text=response.get("text", ""),
            vector=response.get("vector", []),
            attributes=(json.loads(response.get("attributes", "{}"))),
        )
