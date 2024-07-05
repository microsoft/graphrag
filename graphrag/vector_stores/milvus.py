# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Milvus vector storage implementation package."""

from typing import Any

from pymilvus import DataType, MilvusClient

from graphrag.model.types import TextEmbedder

from .base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class MilvusError(Exception):
    """An exception class for Milvus errors."""


class MilvusVectorStore(BaseVectorStore):
    """The Milvus vector storage implementation."""

    def connect(self, **kwargs: Any) -> Any:
        """Connect to the vector storage."""
        self.db_connection = MilvusClient(**kwargs)
        self._id_field = "_id"
        self._text_field = "_text"
        self._vector_field = "_vector"

    def load_documents(
            self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into vector storage."""
        if self.db_connection is None:
            msg = "db_connection not set. Call connect() first."
            raise MilvusError(msg)

        collection_exists = self.db_connection.has_collection(self.collection_name)

        if collection_exists and overwrite:
            self.db_connection.drop_collection(self.collection_name)
            collection_exists = False

        if not collection_exists:
            if not isinstance(documents[0].vector, list):
                return
            dimension = len(documents[0].vector)
            schema = MilvusClient.create_schema(
                auto_id=False,
                enable_dynamic_field=True,
            )
            if isinstance(documents[0].id, str):
                id_field_type = DataType.VARCHAR
            else:
                id_field_type = DataType.INT64
            schema.add_field(field_name=self._id_field, datatype=id_field_type,
                             max_length=65535, is_primary=True)
            schema.add_field(field_name=self._text_field, datatype=DataType.VARCHAR,
                             max_length=65535)
            schema.add_field(field_name=self._vector_field,
                             datatype=DataType.FLOAT_VECTOR,
                             dim=dimension)

            index_params = self.db_connection.prepare_index_params()
            index_params.add_index(
                field_name=self._vector_field,
                index_name=self._vector_field,
                index_type="AUTOINDEX",
                metric_type="IP",
            )
            self.db_connection.create_collection(
                collection_name=self.collection_name,
                schema=schema,
                index_params=index_params,
                consistency_level="Strong"
            )

        data = []
        for document in documents:
            if document.vector is None:
                continue
            entity_data = {
                self._id_field: document.id,
                self._text_field: document.text if document.text else "",
                self._vector_field: document.vector,
            }
            entity_data.update(document.attributes)
            data.append(entity_data)

        self.db_connection.insert(
            collection_name=self.collection_name,
            data=data,
        )

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        if len(include_ids) == 0:
            self.query_filter = ""
        else:
            if isinstance(include_ids[0], str):
                id_filter = ", ".join([f"'{id}'" for id in include_ids])
                self.query_filter = f"{self._id_field} in [{id_filter}]"
            else:
                self.query_filter = (
                    f"{self._id_field} in [{', '.join([str(id) for id in include_ids])}]"
                )
        return self.query_filter

    def similarity_search_by_vector(
            self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self.db_connection is None:
            msg = "db_connection not set. Call connect() first."
            raise MilvusError(msg)
        if not self.db_connection.has_collection(self.collection_name):
            return []

        search_res = self.db_connection.search(
            collection_name=self.collection_name,
            anns_field=self._vector_field,
            data=[query_embedding],
            filter=self.query_filter,
            limit=k,
            output_fields=["*"],
        )[0]

        final_results = []
        for res in search_res:
            res_entity: dict = res["entity"]
            _id = res_entity.pop(self._id_field)
            text = res_entity.pop(self._text_field)
            vector = res_entity.pop(self._vector_field)
            final_results.append(
                VectorStoreSearchResult(
                    document=VectorStoreDocument(
                        id=_id,
                        text=text,
                        vector=vector,
                        attributes=res_entity,
                    ),
                    score=res["distance"],
                )
            )

        return final_results

    def similarity_search_by_text(
            self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a similarity search using a given input text."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        return []
