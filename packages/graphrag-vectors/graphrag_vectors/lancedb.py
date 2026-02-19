# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The LanceDB vector storage implementation package."""

from typing import Any

import lancedb
import numpy as np
import pyarrow as pa

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


class LanceDBVectorStore(VectorStore):
    """LanceDB vector storage implementation."""

    def __init__(self, db_uri: str = "lancedb", **kwargs: Any):
        super().__init__(**kwargs)
        self.db_uri = db_uri

    def connect(self) -> Any:
        """Connect to the vector storage."""
        self.db_connection = lancedb.connect(self.db_uri)

        if self.index_name and self.index_name in self.db_connection.table_names():
            self.document_collection = self.db_connection.open_table(
                self.index_name
            )

    def create_index(self) -> None:
        """Create index."""
        dummy_vector = np.zeros(self.vector_size, dtype=np.float32)
        flat_array = pa.array(dummy_vector, type=pa.float32())
        vector_column = pa.FixedSizeListArray.from_arrays(
            flat_array, self.vector_size
        )

        types = {
            "str": (pa.string, "___DUMMY___"),
            "int": (pa.int64, 1),
            "float": (pa.float32, 1.0),
            "bool": (pa.bool_, True),
        }
        others = {}
        for field_name, field_type in self.fields.items():
            pa_type, dummy_value = types[field_type]
            others[field_name] = pa.array([dummy_value], type=pa_type())

        data = pa.table(
            {
                self.id_field: pa.array(["__DUMMY__"], type=pa.string()),
                self.vector_field: vector_column,
                self.create_date_field: pa.array(
                    ["___DUMMY___"], type=pa.string()
                ),
                self.update_date_field: pa.array(
                    ["___DUMMY___"], type=pa.string()
                ),
                **others,
            }
        )

        self.document_collection = self.db_connection.create_table(
            self.index_name if self.index_name else "",
            data=data,
            mode="overwrite",
            schema=data.schema,
        )

        # Create index now that schema exists
        self.document_collection.create_index(
            vector_column_name=self.vector_field, index_type="IVF_FLAT"
        )

        # Remove the dummy document used to set up the schema
        self.document_collection.delete(f"{self.id_field} = '__DUMMY__'")

    def insert(self, document: VectorStoreDocument) -> None:
        """Insert a single document into LanceDB."""
        self._prepare_document(document)
        if document.vector is not None:
            vector = np.array(document.vector, dtype=np.float32)
            flat_array = pa.array(vector, type=pa.float32())
            vector_column = pa.FixedSizeListArray.from_arrays(
                flat_array, self.vector_size
            )

            others = {}
            for field_name in self.fields:
                others[field_name] = (
                    document.data.get(field_name) if document.data else None
                )

            data = pa.table(
                {
                    self.id_field: pa.array([document.id], type=pa.string()),
                    self.vector_field: vector_column,
                    self.create_date_field: pa.array(
                        [document.create_date], type=pa.string()
                    ),
                    self.update_date_field: pa.array(
                        [document.update_date], type=pa.string()
                    ),
                    **{
                        field_name: pa.array([value])
                        for field_name, value in others.items()
                    },
                }
            )

            self.document_collection.add(data)

    def _extract_data(
        self, doc: dict[str, Any], select: list[str] | None = None
    ) -> dict[str, Any]:
        """Extract additional field data from a document response."""
        fields_to_extract = (
            select if select is not None else list(self.fields.keys())
        )
        return {
            field_name: doc[field_name]
            for field_name in fields_to_extract
            if field_name in doc
        }

    def _compile_filter(self, expr: FilterExpr) -> str:
        """Compile a FilterExpr into a LanceDB SQL WHERE clause."""
        match expr:
            case Condition():
                return self._compile_condition(expr)
            case AndExpr():
                parts = [self._compile_filter(e) for e in expr.and_]
                return " AND ".join(f"({p})" for p in parts)
            case OrExpr():
                parts = [self._compile_filter(e) for e in expr.or_]
                return " OR ".join(f"({p})" for p in parts)
            case NotExpr():
                inner = self._compile_filter(expr.not_)
                return f"NOT ({inner})"
            case _:
                msg = f"Unsupported filter expression type: {type(expr)}"
                raise ValueError(msg)

    def _compile_condition(self, cond: Condition) -> str:
        """Compile a single Condition to LanceDB SQL syntax."""
        field = cond.field
        value = cond.value

        def quote(v: Any) -> str:
            return f"'{v}'" if isinstance(v, str) else str(v)

        match cond.operator:
            case Operator.eq:
                return f"{field} = {quote(value)}"
            case Operator.ne:
                return f"{field} != {quote(value)}"
            case Operator.gt:
                return f"{field} > {quote(value)}"
            case Operator.gte:
                return f"{field} >= {quote(value)}"
            case Operator.lt:
                return f"{field} < {quote(value)}"
            case Operator.lte:
                return f"{field} <= {quote(value)}"
            case Operator.in_:
                items = ", ".join(quote(v) for v in value)
                return f"{field} IN ({items})"
            case Operator.not_in:
                items = ", ".join(quote(v) for v in value)
                return f"{field} NOT IN ({items})"
            case Operator.contains:
                return f"{field} LIKE '%{value}%'"
            case Operator.startswith:
                return f"{field} LIKE '{value}%'"
            case Operator.endswith:
                return f"{field} LIKE '%{value}'"
            case Operator.exists:
                return (
                    f"{field} IS NOT NULL" if value else f"{field} IS NULL"
                )
            case _:
                msg = f"Unsupported operator for LanceDB: {cond.operator}"
                raise ValueError(msg)

    def similarity_search_by_vector(
        self,
        query_embedding: list[float] | np.ndarray,
        k: int = 10,
        select: list[str] | None = None,
        filters: FilterExpr | None = None,
        include_vectors: bool = True,
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        query_embedding = np.array(query_embedding, dtype=np.float32)

        query = self.document_collection.search(
            query=query_embedding, vector_column_name=self.vector_field
        )

        if filters is not None:
            query = query.where(self._compile_filter(filters), prefilter=True)

        docs = query.limit(k).to_list()
        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc[self.id_field],
                    vector=doc[self.vector_field] if include_vectors else None,
                    data=self._extract_data(doc, select),
                    create_date=doc.get(self.create_date_field),
                    update_date=doc.get(self.update_date_field),
                ),
                score=1 - abs(float(doc["_distance"])),
            )
            for doc in docs
        ]

    def search_by_id(
        self,
        id: str,
        select: list[str] | None = None,
        include_vectors: bool = True,
    ) -> VectorStoreDocument:
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
            vector=doc[self.vector_field] if include_vectors else None,
            data=self._extract_data(doc, select),
            create_date=doc.get(self.create_date_field),
            update_date=doc.get(self.update_date_field),
        )

    def count(self) -> int:
        """Return the total number of documents in the store."""
        return self.document_collection.count_rows()

    def remove(self, ids: list[str]) -> None:
        """Remove documents by their IDs."""
        id_list = ", ".join(f"'{id}'" for id in ids)
        self.document_collection.delete(f"{self.id_field} IN ({id_list})")

    def update(self, document: VectorStoreDocument) -> None:
        """Update an existing document in the store."""
        self._prepare_update(document)

        # Build update values
        updates: dict[str, Any] = {
            self.update_date_field: document.update_date,
        }
        if document.vector is not None:
            updates[self.vector_field] = np.array(
                document.vector, dtype=np.float32
            )
        if document.data:
            for field_name in self.fields:
                if field_name in document.data:
                    updates[field_name] = document.data[field_name]

        self.document_collection.update(
            where=f"{self.id_field} = '{document.id}'",
            values=updates,
        )
