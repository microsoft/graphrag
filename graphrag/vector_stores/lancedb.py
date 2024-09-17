# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The LanceDB vector storage implementation package."""

import lancedb as lancedb  # noqa: I001 (Ruff was breaking on this file imports, even tho they were sorted and passed local tests)
from graphrag.model.community_report import CommunityReport
from graphrag.model.entity import Entity
from graphrag.model.types import TextEmbedder
from graphrag.model import TextUnit

import json
from typing import Any

import pyarrow as pa

from .base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class LanceDBVectorStore(BaseVectorStore):
    """The LanceDB vector storage implementation."""

    def connect(self, **kwargs: Any) -> Any:
        """Connect to the vector storage."""
        db_uri = kwargs.get("db_uri", "./lancedb")
        self.db_connection = lancedb.connect(db_uri)  # type: ignore

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into vector storage."""
        data = [
            {
                "id": document.id,
                "text": document.text,
                "vector": document.vector,
                "attributes": json.dumps(document.attributes),
            }
            for document in documents
            if document.vector is not None
        ]

        if len(data) == 0:
            data = None

        schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("text", pa.string()),
            pa.field("vector", pa.list_(pa.float64())),
            pa.field("attributes", pa.string()),
        ])
        if overwrite:
            if data:
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
            if data:
                self.document_collection.add(data)

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        if len(include_ids) == 0:
            self.query_filter = None
        else:
            if isinstance(include_ids[0], str):
                id_filter = ", ".join([f"'{id}'" for id in include_ids])
                self.query_filter = f"id in ({id_filter})"
            else:
                self.query_filter = (
                    f"id in ({', '.join([str(id) for id in include_ids])})"
                )
        return self.query_filter

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self.query_filter:
            docs = (
                self.document_collection.search(query=query_embedding)
                .where(self.query_filter, prefilter=True)
                .limit(k)
                .to_list()
            )
        else:
            docs = (
                self.document_collection.search(query=query_embedding)
                .limit(k)
                .to_list()
            )
        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc["id"],
                    text=doc["text"],
                    vector=doc["vector"],
                    attributes=json.loads(doc["attributes"]),
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

    def load_entities(self, entities: list[Entity], overwrite: bool = True) -> None:
        raise NotImplementedError("Loading entities is not supported for LanceDB")

    def get_extracted_entities(self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[Entity]:
        raise NotImplementedError("Extracting entities is not supported for LanceDB")

    def load_reports(self, reports: list[CommunityReport], overwrite: bool = True) -> None:
        raise NotImplementedError("Loading reports is not supported for LanceDB")

    def load_text_units(self, units: list[TextUnit], overwrite: bool = True) -> None:
        raise NotImplementedError("load_text_units(): Unsupported for this vector store.")

    def get_extracted_reports(self, community_ids: list[int], **kwargs: Any) -> list[CommunityReport]:
        raise NotImplementedError("Extracting community reports is not supported for LanceDB")

    def setup_entities(self) -> None:
        raise NotImplementedError("Setting up entities is not supported for LanceDB")

    def setup_reports(self) -> None:
        raise NotImplementedError("Setting up community reports is not supported for LanceDB")

    def setup_text_units(self) -> None:
        raise NotImplementedError("setup_text_units(): Unsupported for this vector store.")

    def unload_entities(self) -> None:
        raise NotImplementedError("unload_entities(): Unsupported for this vector store.")
