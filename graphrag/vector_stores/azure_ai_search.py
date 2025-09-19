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

from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig
from graphrag.data_model.types import TextEmbedder
from graphrag.vector_stores.base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class AzureAISearchVectorStore(BaseVectorStore):
    """Azure AI Search vector storage implementation."""

    index_client: SearchIndexClient

    def __init__(
        self, vector_store_schema_config: VectorStoreSchemaConfig, **kwargs: Any
    ) -> None:
        super().__init__(
            vector_store_schema_config=vector_store_schema_config, **kwargs
        )

    def connect(self, **kwargs: Any) -> Any:
        """Connect to AI search vector storage."""
        url = kwargs["url"]
        api_key = kwargs.get("api_key")
        audience = kwargs.get("audience")

        self.vector_search_profile_name = kwargs.get(
            "vector_search_profile_name", "vectorSearchProfile"
        )

        if url:
            audience_arg = {"audience": audience} if audience and not api_key else {}
            self.db_connection = SearchClient(
                endpoint=url,
                index_name=self.index_name if self.index_name else "",
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
            if (
                self.index_name is not None
                and self.index_name in self.index_client.list_index_names()
            ):
                self.index_client.delete_index(self.index_name)

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
                name=self.index_name if self.index_name else "",
                fields=[
                    SimpleField(
                        name=self.id_field,
                        type=SearchFieldDataType.String,
                        key=True,
                    ),
                    SearchField(
                        name=self.vector_field,
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True,
                        hidden=False,  # DRIFT needs to return the vector for client-side similarity
                        vector_search_dimensions=self.vector_size,
                        vector_search_profile_name=self.vector_search_profile_name,
                    ),
                    SearchableField(
                        name=self.text_field, type=SearchFieldDataType.String
                    ),
                    SimpleField(
                        name=self.attributes_field,
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
                self.id_field: doc.id,
                self.vector_field: doc.vector,
                self.text_field: doc.text,
                self.attributes_field: json.dumps(doc.attributes),
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
        self.query_filter = f"search.in({self.id_field}, '{id_filter}', ',')"

        # Returning to keep consistency with other methods, but not needed
        # TODO: Refactor on a future PR
        return self.query_filter

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        vectorized_query = VectorizedQuery(
            vector=query_embedding, k_nearest_neighbors=k, fields=self.vector_field
        )

        response = self.db_connection.search(
            vector_queries=[vectorized_query],
        )

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc.get(self.id_field, ""),
                    text=doc.get(self.text_field, ""),
                    vector=doc.get(self.vector_field, []),
                    attributes=(json.loads(doc.get(self.attributes_field, "{}"))),
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
            id=response.get(self.id_field, ""),
            text=response.get(self.text_field, ""),
            vector=response.get(self.vector_field, []),
            attributes=(json.loads(response.get(self.attributes_field, "{}"))),
        )
