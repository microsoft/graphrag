# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The LanceDB vector storage implementation package."""

from typing import Any

import lancedb
import numpy as np
import pyarrow as pa

from graphrag_vectors.vector_store import (
    VectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class LanceDBVectorStore(VectorStore):
    """LanceDB vector storage implementation."""

    def __init__(self, db_uri: str = "lancedb", **kwargs: Any):
        super().__init__(**kwargs)
        self.db_uri = db_uri

    def connect(self) -> Any:
        """Connect to the vector storage."""
        self.db_connection = lancedb.connect(self.db_uri)
        if self.index_name in self.db_connection.table_names():
            self.document_collection = self.db_connection.open_table(self.index_name)

    def create_index(self) -> None:
        """Create index."""
        dummy_vector = np.zeros(self.vector_size, dtype=np.float32)
        flat_array = pa.array(dummy_vector, type=pa.float32())
        vector_column = pa.FixedSizeListArray.from_arrays(flat_array, self.vector_size)

        types = {
            "string": (pa.string, "___DUMMY___"),
            "integer": (pa.int64, 1),
            "float": (pa.float32, 1.0),
        }
        others = {}
        for field, field_type in self.fields.items():
            pa_type, dummy_value = types[field_type]
            others[field] = pa.array([dummy_value], type=pa_type())

        data = pa.table({
            self.id_field: pa.array(["__DUMMY__"], type=pa.string()),
            self.vector_field: vector_column,
            **others,
        })

        self.document_collection = self.db_connection.create_table(
            self.index_name,
            data=data,
            mode="overwrite",
            schema=data.schema,
        )

        # Step 5: Create index now that schema exists
        self.document_collection.create_index(
            vector_column_name=self.vector_field, index_type="IVF_FLAT"
        )

    def load_documents(self, documents: list[VectorStoreDocument]) -> None:
        """Load documents into vector storage."""
        # we created a dummy document to set up the schema in .create_index; now remove it
        self.document_collection.delete(f"{self.id_field} = '__DUMMY__'")

        # Step 1: Prepare data columns manually to ensure correct schema for vectors
        ids = []
        vectors = []
        others = []

        for document in documents:
            ids.append(document.id)
            vectors.append(np.array(document.vector, dtype=np.float32))
            other = {}
            for field in self.fields:
                other[field] = document.data.get(field) if document.data else None
            others.append(other)

        # Step 2: Handle empty case
        if len(ids) > 0:
            # Step 3: Flatten the vectors and build FixedSizeListArray manually
            flat_vector = np.concatenate(vectors).astype(np.float32)
            flat_array = pa.array(flat_vector, type=pa.float32())
            vector_column = pa.FixedSizeListArray.from_arrays(
                flat_array, self.vector_size
            )

            # Step 4: Create PyArrow table (let schema be inferred)
            data = pa.table({
                self.id_field: pa.array(ids, type=pa.string()),
                self.vector_field: vector_column,
                **{
                    field: pa.array([other.get(field) for other in others])
                    for field in self.fields
                },
            })

            self.document_collection.add(data)

    def _extract_data(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Extract additional field data from a document response."""
        return {
            field_name: doc[field_name]
            for field_name in self.fields
            if field_name in doc
        }

    def similarity_search_by_vector(
        self, query_embedding: list[float] | np.ndarray, k: int = 10
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
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
                    vector=doc[self.vector_field],
                    data=self._extract_data(doc),
                ),
                score=1 - abs(float(doc["_distance"])),
            )
            for doc in docs
        ]

    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        result = (
            self.document_collection.search()
            .where(f"{self.id_field} == '{id}'", prefilter=True)
            .to_list()
        )
        if result is None or len(result) == 0:
            msg = f"Document with id '{id}' not found."
            raise IndexError(msg)
        doc = result[0]
        return VectorStoreDocument(
            id=doc[self.id_field],
            vector=doc[self.vector_field],
            data=self._extract_data(doc),
        )
