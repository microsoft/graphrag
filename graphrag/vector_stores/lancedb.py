# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The LanceDB vector storage implementation package."""

import json  # noqa: I001
from typing import Any
import pyarrow as pa
import numpy as np
from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig
from graphrag.data_model.types import TextEmbedder

from graphrag.vector_stores.base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)
import lancedb


class LanceDBVectorStore(BaseVectorStore):
    """LanceDB vector storage implementation."""

    def __init__(
        self, vector_store_schema_config: VectorStoreSchemaConfig, **kwargs: Any
    ) -> None:
        super().__init__(
            vector_store_schema_config=vector_store_schema_config, **kwargs
        )

    def connect(self, **kwargs: Any) -> Any:
        """Connect to the vector storage."""
        self.db_connection = lancedb.connect(kwargs["db_uri"])

        if self.index_name and self.index_name in self.db_connection.table_names():
            self.document_collection = self.db_connection.open_table(self.index_name)

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into vector storage."""
        # Step 1: Prepare data columns manually
        ids = []
        texts = []
        vectors = []
        attributes = []

        for document in documents:
            self.vector_size = (
                len(document.vector) if document.vector else self.vector_size
            )
            if document.vector is not None and len(document.vector) == self.vector_size:
                ids.append(document.id)
                texts.append(document.text)
                vectors.append(np.array(document.vector, dtype=np.float32))
                attributes.append(json.dumps(document.attributes))

        # Step 2: Handle empty case
        if len(ids) == 0:
            data = None
        else:
            # Step 3: Flatten the vectors and build FixedSizeListArray manually
            flat_vector = np.concatenate(vectors).astype(np.float32)
            flat_array = pa.array(flat_vector, type=pa.float32())
            vector_column = pa.FixedSizeListArray.from_arrays(
                flat_array, self.vector_size
            )

            # Step 4: Create PyArrow table (let schema be inferred)
            data = pa.table({
                self.id_field: pa.array(ids, type=pa.string()),
                self.text_field: pa.array(texts, type=pa.string()),
                self.vector_field: vector_column,
                self.attributes_field: pa.array(attributes, type=pa.string()),
            })

        # NOTE: If modifying the next section of code, ensure that the schema remains the same.
        #       The pyarrow format of the 'vector' field may change if the order of operations is changed
        #       and will break vector search.
        if overwrite:
            if data:
                self.document_collection = self.db_connection.create_table(
                    self.index_name if self.index_name else "",
                    data=data,
                    mode="overwrite",
                    schema=data.schema,
                )
            else:
                self.document_collection = self.db_connection.create_table(
                    self.index_name if self.index_name else "", mode="overwrite"
                )
            self.document_collection.create_index(
                vector_column_name=self.vector_field, index_type="IVF_FLAT"
            )
        else:
            # add data to existing table
            self.document_collection = self.db_connection.open_table(
                self.index_name if self.index_name else ""
            )
            if data:
                self.document_collection.add(data)

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        if len(include_ids) == 0:
            self.query_filter = None
        else:
            if isinstance(include_ids[0], str):
                id_filter = ", ".join([f"'{id}'" for id in include_ids])
                self.query_filter = f"{self.id_field} in ({id_filter})"
            else:
                self.query_filter = (
                    f"{self.id_field} in ({', '.join([str(id) for id in include_ids])})"
                )
        return self.query_filter

    def similarity_search_by_vector(
        self, query_embedding: list[float] | np.ndarray, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self.query_filter:
            docs = (
                self.document_collection.search(
                    query=query_embedding, vector_column_name=self.vector_field
                )
                .where(self.query_filter, prefilter=True)
                .limit(k)
                .to_list()
            )
        else:
            query_embedding = np.array(query_embedding, dtype=np.float32)

            docs = (
                self.document_collection.search(
                    query=query_embedding, vector_column_name=self.vector_field
                )
                .limit(k)
                .to_list()
            )
        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc[self.id_field],
                    text=doc[self.text_field],
                    vector=doc[self.vector_field],
                    attributes=json.loads(doc[self.attributes_field]),
                ),
                score=1 - abs(float(doc["_distance"])),
            )
            for doc in docs
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a similarity search using a given input text."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        return []

    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        doc = (
            self.document_collection.search()
            .where(f"{self.id_field} == '{id}'", prefilter=True)
            .to_list()
        )
        if doc:
            return VectorStoreDocument(
                id=doc[0][self.id_field],
                text=doc[0][self.text_field],
                vector=doc[0][self.vector_field],
                attributes=json.loads(doc[0][self.attributes_field]),
            )
        return VectorStoreDocument(id=id, text=None, vector=None)
