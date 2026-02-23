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

from graphrag_vectors.filtering import (
    AndExpr,
    Condition,
    FilterExpr,
    NotExpr,
    Operator,
    OrExpr,
)
from graphrag_vectors.vector_store import (
    VectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)

# Mapping from field type strings to Azure AI Search data types
FIELD_TYPE_MAPPING: dict[str, SearchFieldDataType] = {
    "str": SearchFieldDataType.String,
    "int": SearchFieldDataType.Int64,
    "float": SearchFieldDataType.Double,
    "bool": SearchFieldDataType.Boolean,
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
            SimpleField(
                name=self.create_date_field,
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SimpleField(
                name=self.update_date_field,
                type=SearchFieldDataType.String,
                filterable=True,
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

    def insert(self, document: VectorStoreDocument) -> None:
        """Insert a single document into Azure AI Search."""
        self._prepare_document(document)
        if document.vector is not None:
            doc_dict = {
                self.id_field: document.id,
                self.vector_field: document.vector,
                self.create_date_field: document.create_date,
                self.update_date_field: document.update_date,
            }
            # Add additional fields if they exist in the document data
            if document.data:
                for field_name in self.fields:
                    if field_name in document.data:
                        doc_dict[field_name] = document.data[field_name]
            self.db_connection.upload_documents([doc_dict])

    def _compile_filter(self, expr: FilterExpr) -> str:
        """Compile a FilterExpr into an Azure AI Search OData filter string."""
        match expr:
            case Condition():
                return self._compile_condition(expr)
            case AndExpr():
                parts = [self._compile_filter(e) for e in expr.and_]
                return " and ".join(f"({p})" for p in parts)
            case OrExpr():
                parts = [self._compile_filter(e) for e in expr.or_]
                return " or ".join(f"({p})" for p in parts)
            case NotExpr():
                inner = self._compile_filter(expr.not_)
                return f"not ({inner})"
            case _:
                msg = f"Unsupported filter expression type: {type(expr)}"
                raise ValueError(msg)

    def _compile_condition(self, cond: Condition) -> str:
        """Compile a single Condition to OData filter syntax."""
        field = cond.field
        value = cond.value

        def quote(v: Any) -> str:
            return (
                f"'{v}'"
                if isinstance(v, str)
                else str(v).lower()
                if isinstance(v, bool)
                else str(v)
            )

        match cond.operator:
            case Operator.eq:
                return f"{field} eq {quote(value)}"
            case Operator.ne:
                return f"{field} ne {quote(value)}"
            case Operator.gt:
                return f"{field} gt {quote(value)}"
            case Operator.gte:
                return f"{field} ge {quote(value)}"
            case Operator.lt:
                return f"{field} lt {quote(value)}"
            case Operator.lte:
                return f"{field} le {quote(value)}"
            case Operator.in_:
                items = " or ".join(f"{field} eq {quote(v)}" for v in value)
                return f"({items})"
            case Operator.not_in:
                items = " and ".join(f"{field} ne {quote(v)}" for v in value)
                return f"({items})"
            case Operator.contains:
                return f"search.ismatch('{value}', '{field}')"
            case Operator.startswith:
                return f"search.ismatch('{value}*', '{field}')"
            case Operator.endswith:
                return f"search.ismatch('*{value}', '{field}')"
            case Operator.exists:
                return f"{field} ne null" if value else f"{field} eq null"
            case _:
                msg = f"Unsupported operator for Azure AI Search: {cond.operator}"
                raise ValueError(msg)

    def _extract_data(
        self, doc: dict[str, Any], select: list[str] | None = None
    ) -> dict[str, Any]:
        """Extract additional field data from a document response."""
        fields_to_extract = select if select is not None else list(self.fields.keys())
        return {
            field_name: doc[field_name]
            for field_name in fields_to_extract
            if field_name in doc
        }

    def similarity_search_by_vector(
        self,
        query_embedding: list[float],
        k: int = 10,
        select: list[str] | None = None,
        filters: FilterExpr | None = None,
        include_vectors: bool = True,
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        vectorized_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=k,
            fields=self.vector_field,
        )

        # Build the list of fields to select - always include id, vector, and timestamps
        fields_to_select = [
            self.id_field,
            self.create_date_field,
            self.update_date_field,
        ]
        if include_vectors:
            fields_to_select.append(self.vector_field)
        if select is not None:
            fields_to_select.extend(select)
        else:
            fields_to_select.extend(self.fields.keys())

        # Build OData filter string
        filter_str = self._compile_filter(filters) if filters is not None else None

        response = self.db_connection.search(
            vector_queries=[vectorized_query],
            select=fields_to_select,
            filter=filter_str,
        )

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc.get(self.id_field, ""),
                    vector=doc.get(self.vector_field, []) if include_vectors else None,
                    data=self._extract_data(doc, select),
                    create_date=doc.get(self.create_date_field),
                    update_date=doc.get(self.update_date_field),
                ),
                # Cosine similarity between 0.333 and 1.000
                # https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking#scores-in-a-hybrid-search-results
                score=doc["@search.score"],
            )
            for doc in response
        ]

    def search_by_id(
        self,
        id: str,
        select: list[str] | None = None,
        include_vectors: bool = True,
    ) -> VectorStoreDocument:
        """Search for a document by id."""
        # Build the list of fields to select - always include id, vector, and timestamps
        fields_to_select = [
            self.id_field,
            self.create_date_field,
            self.update_date_field,
        ]
        if include_vectors:
            fields_to_select.append(self.vector_field)
        if select is not None:
            fields_to_select.extend(select)
        else:
            fields_to_select.extend(self.fields.keys())

        response = self.db_connection.get_document(id, selected_fields=fields_to_select)
        return VectorStoreDocument(
            id=response[self.id_field],
            vector=response.get(self.vector_field, []) if include_vectors else None,
            data=self._extract_data(response, select),
            create_date=response.get(self.create_date_field),
            update_date=response.get(self.update_date_field),
        )

    def count(self) -> int:
        """Return the total number of documents in the store."""
        return self.db_connection.get_document_count()

    def remove(self, ids: list[str]) -> None:
        """Remove documents by their IDs."""
        batch = [{"@search.action": "delete", self.id_field: id} for id in ids]
        self.db_connection.upload_documents(batch)

    def update(self, document: VectorStoreDocument) -> None:
        """Update an existing document in the store."""
        self._prepare_update(document)

        doc: dict[str, Any] = {
            "@search.action": "merge",
            self.id_field: document.id,
            self.update_date_field: document.update_date,
        }

        if document.vector is not None:
            doc[self.vector_field] = document.vector

        if document.data:
            for field_name in self.fields:
                if field_name in document.data:
                    doc[field_name] = document.data[field_name]

        self.db_connection.upload_documents([doc])
