# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the Azure AI Search  vector store implementation."""

from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from graphrag_vectors.vector_store import (
    VectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)

# Mapping from field type strings to Azure AI Search data types
FIELD_TYPE_MAPPING: dict[str, SearchFieldDataType] = {
    "string": SearchFieldDataType.String,
    "int": SearchFieldDataType.Int64,
    "float": SearchFieldDataType.Double,
}


class AzureAISearchVectorStore(VectorStore):
    """Azure AI Search vector storage implementation."""

    index_client: SearchIndexClient

    def __init__(
        self,
        url: str,
        api_key: str | None = None,
        audience: str | None = None,
        vector_search_profile_name: str = "vectorSearchProfile",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if not url:
            msg = "url must be provided for Azure AI Search."
            raise ValueError(msg)
        self.url = url
        self.api_key = api_key
        self.audience = audience
        self.vector_search_profile_name = vector_search_profile_name

    def connect(self) -> Any:
        """Connect to AI search vector storage."""
        audience_arg = (
            {"audience": self.audience} if self.audience and not self.api_key else {}
        )
        self.db_connection = SearchClient(
            endpoint=self.url,
            index_name=self.index_name,
            credential=(
                AzureKeyCredential(self.api_key)
                if self.api_key
                else DefaultAzureCredential()
            ),
            **audience_arg,
        )
        self.index_client = SearchIndexClient(
            endpoint=self.url,
            credential=(
                AzureKeyCredential(self.api_key)
                if self.api_key
                else DefaultAzureCredential()
            ),
            **audience_arg,
        )

    def create_index(self) -> None:
        """Load documents into an Azure AI Search index."""
        if self.index_name in self.index_client.list_index_names():
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
        # Build the list of fields
        fields = [
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
        ]

        # Add additional fields from the fields dictionary
        for field_name, field_type in self.fields.items():
            fields.append(
                SimpleField(
                    name=field_name,
                    type=FIELD_TYPE_MAPPING[field_type],
                    filterable=True,
                )
            )

        # Configure the index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search,
        )
        self.index_client.create_or_update_index(
            index,
        )

    def load_documents(self, documents: list[VectorStoreDocument]) -> None:
        """Load documents into an Azure AI Search index."""
        batch = []
        for doc in documents:
            if doc.vector is not None:
                doc_dict = {
                    self.id_field: doc.id,
                    self.vector_field: doc.vector,
                }
                # Add additional fields if they exist in the document data
                if doc.data:
                    for field_name in self.fields:
                        if field_name in doc.data:
                            doc_dict[field_name] = doc.data[field_name]
                batch.append(doc_dict)

        if len(batch) > 0:
            self.db_connection.upload_documents(batch)

    def _extract_data(self, doc: dict[str, Any], select: list[str] | None = None) -> dict[str, Any]:
        """Extract additional field data from a document response."""
        fields_to_extract = select if select is not None else list(self.fields.keys())
        return {
            field_name: doc[field_name]
            for field_name in fields_to_extract
            if field_name in doc
        }

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, select: list[str] | None = None
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        vectorized_query = VectorizedQuery(
            vector=query_embedding, k_nearest_neighbors=k, fields=self.vector_field
        )

        # Build the list of fields to select - always include id and vector fields
        fields_to_select = [self.id_field, self.vector_field]
        if select is not None:
            fields_to_select.extend(select)
        else:
            fields_to_select.extend(self.fields.keys())

        response = self.db_connection.search(
            vector_queries=[vectorized_query],
            select=fields_to_select,
        )

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc.get(self.id_field, ""),
                    vector=doc.get(self.vector_field, []),
                    data=self._extract_data(doc, select),
                ),
                # Cosine similarity between 0.333 and 1.000
                # https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking#scores-in-a-hybrid-search-results
                score=doc["@search.score"],
            )
            for doc in response
        ]

    def search_by_id(self, id: str, select: list[str] | None = None) -> VectorStoreDocument:
        """Search for a document by id."""
        # Build the list of fields to select - always include id and vector fields
        fields_to_select = [self.id_field, self.vector_field]
        if select is not None:
            fields_to_select.extend(select)
        else:
            fields_to_select.extend(self.fields.keys())

        response = self.db_connection.get_document(id, selected_fields=fields_to_select)
        return VectorStoreDocument(
            id=response[self.id_field],
            vector=response.get(self.vector_field, []),
            data=self._extract_data(response, select),
        )
