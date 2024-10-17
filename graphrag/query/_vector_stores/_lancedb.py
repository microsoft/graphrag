# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import json
import typing
import typing_extensions

import lancedb  # type: ignore
import pyarrow as pa  # type: ignore

from . import _base_vector_store


class LanceDBVectorStore(_base_vector_store.BaseVectorStore):
    """The LanceDB vector storage implementation."""
    collection_name: str
    db_connection: lancedb.DBConnection  # type: ignore
    document_collection: lancedb.table.Table  # type: ignore
    query_filter: typing.Optional[str] = None

    def __init__(self, collection_name: str, uri: str = "./lancedb", **kwargs: typing.Any) -> None:
        """Initialize the LanceDB vector storage."""
        super().__init__(collection_name, **kwargs)
        self.db_connection = lancedb.connect(uri)  # type: ignore

    @typing_extensions.override
    def load_documents(
        self, documents: typing.List[_base_vector_store.VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into vector storage."""
        data = [
            {
                "id":         document.id,
                "text":       document.text,
                "vector":     document.vector,
                "attributes": json.dumps(document.attributes),
            } for document in documents if document.vector is not None
        ]

        schema = pa.schema(
            [
                pa.field("id", pa.string()),
                pa.field("text", pa.string()),
                pa.field("vector", pa.list_(pa.float64())),
                pa.field("attributes", pa.string()),
            ]
        )
        if overwrite:
            if data.__len__():
                self.document_collection = self.db_connection.create_table(
                    self.collection_name, data=data, mode="overwrite"
                )
            else:
                self.document_collection = self.db_connection.create_table(
                    self.collection_name, schema=schema, mode="overwrite"
                )
        else:
            # add data to existing table
            self.document_collection = self.db_connection.open_table(
                self.collection_name
            )
            if data.__len__():
                self.document_collection.add(data)

    @typing_extensions.override
    def filter_by_id(self, include_ids: typing.List[str] | typing.List[int]) -> typing.Optional[str]:
        """Build a query filter to filter documents by id."""
        if len(include_ids) == 0:
            self.query_filter = None
        else:
            if isinstance(include_ids[0], str):
                id_filter = ", ".join([f"'{id}'" for id in include_ids])
                self.query_filter = f"id in ({id_filter})"
            else:
                self.query_filter = f"id in ({', '.join([str(id) for id in include_ids])})"

        return self.query_filter

    @typing_extensions.override
    def similarity_search_by_vector(
        self, query_embedding: typing.List[float], k: int = 10, **kwargs: typing.Any
    ) -> typing.List[_base_vector_store.VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self.query_filter:
            docs = (
                self.document_collection.search(query=query_embedding)
                .where(self.query_filter, prefilter=True).limit(k).to_list()
            )
        else:
            docs = self.document_collection.search(query=query_embedding).limit(k).to_list()
        return [
            _base_vector_store.VectorStoreSearchResult(
                document=_base_vector_store.VectorStoreDocument(
                    id=doc["id"],
                    text=doc["text"],
                    vector=doc["vector"],
                    attributes=json.loads(doc["attributes"]),
                ),
                score=1 - abs(float(doc["_distance"])),
            ) for doc in docs
        ]

    @typing_extensions.override
    def similarity_search_by_text(
        self,
        text: str,
        text_embedder: typing.Callable[[str], typing.List[float]],
        k: int = 10,
        **kwargs: typing.Any
    ) -> typing.List[_base_vector_store.VectorStoreSearchResult]:
        """Perform a similarity search using a given input text."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        return []
