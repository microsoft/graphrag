"""Couchbase vector store implementation for GraphRAG."""

import json
import logging
from typing import Any

from couchbase.cluster import Cluster
from couchbase.exceptions import CouchbaseException, DocumentExistsException
from couchbase.options import SearchOptions
from couchbase.result import MultiMutationResult
from couchbase.search import SearchRequest
from couchbase.vector_search import VectorQuery, VectorSearch

from graphrag.model.types import TextEmbedder

from .base import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)

# Set up logger
logger = logging.getLogger(__name__)


class CouchbaseVectorStore(BaseVectorStore):
    """The Couchbase vector storage implementation."""

    def __init__(
        self,
        collection_name: str,
        bucket_name: str,
        scope_name: str = "_default",
        index_name: str = "graphrag_index",
        text_key: str = "text",
        embedding_key: str = "embedding",
        scoped_index: bool = True,
        **kwargs: Any,
    ):
        super().__init__(collection_name, **kwargs)
        self.bucket_name = bucket_name
        self.scope_name = scope_name
        self.index_name = index_name
        self.text_key = text_key
        self.embedding_key = embedding_key
        self.scoped_index = scoped_index
        self.vector_size = kwargs.get("vector_size", DEFAULT_VECTOR_SIZE)
        self._cluster = None
        logger.debug(
            "Initialized CouchbaseVectorStore with collection: %s, bucket: %s, scope: %s, index: %s",
            collection_name,
            bucket_name,
            scope_name,
            index_name,
        )

    def connect(self, **kwargs: Any) -> None:
        """Connect to the Couchbase vector store."""
        connection_string = kwargs.get("connection_string")
        cluster_options = kwargs.get("cluster_options")

        if not isinstance(connection_string, str):
            error_msg = "Connection string must be a string"
            logger.error(error_msg)
            raise TypeError(error_msg)

        try:
            logger.info("Connecting to Couchbase at %s", connection_string)
            self._cluster = Cluster(connection_string, cluster_options)
            self.db_connection = self._cluster
            self.bucket = self._cluster.bucket(self.bucket_name)

            if self.scoped_index and self.scope_name:
                self.scope = self.bucket.scope(self.scope_name)
            else:
                self.scope = self.bucket.default_scope()

            self.document_collection = self.scope.collection(self.collection_name)
            logger.info("Successfully connected to Couchbase")
        except Exception as e:
            error_msg = f"Failed to connect to Couchbase: {e}"
            logger.exception(error_msg)
            raise ConnectionError(error_msg) from e

    def load_documents(self, documents: list[VectorStoreDocument]) -> int:
        """
        Load documents into vector storage.

        :param documents: A list of VectorStoreDocuments to load into the vector store.
        :raises DuplicateDocumentError: If a document with the same ID already exists in the vector store.
        :raises DocumentStoreError: If there's an error writing documents to Couchbase.
        :returns: The number of documents loaded into the vector store.
        """
        logger.info("Loading %d documents into vector storage", len(documents))
        batch = {
            doc.id: {
                self.text_key: doc.text,
                self.embedding_key: doc.vector,
                "attributes": json.dumps(doc.attributes),
            }
            for doc in documents
            if doc.vector is not None
        }

        if not batch:
            logger.warning("No valid documents to load")
            return 0

        try:
            result: MultiMutationResult = self.document_collection.upsert_multi(batch)

            if not result.all_ok and result.exceptions:
                duplicate_ids = []
                other_errors = []
                for doc_id, ex in result.exceptions.items():
                    if isinstance(ex, DocumentExistsException):
                        duplicate_ids.append(doc_id)
                    else:
                        other_errors.append({"id": doc_id, "exception": str(ex)})

                if duplicate_ids:
                    msg = f"IDs '{', '.join(duplicate_ids)}' already exist in the vector store."
                    raise DocumentExistsException(msg)

                if other_errors:
                    msg = f"Failed to load documents into Couchbase. Errors:\n{other_errors}"
                    raise CouchbaseException(msg)

            logger.info("Successfully loaded %d documents", len(batch))
            return len(batch)

        except Exception as e:
            logger.exception("Error occurred while loading documents: %s", e)
            msg = f"Failed to load documents into Couchbase. Error: {e}"
            raise CouchbaseException(msg) from e

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform KNN search by text."""
        logger.info("Performing similarity search by text with k=%d", k)
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        logger.warning("Failed to generate embedding for the query text")
        return []

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform KNN search by vector."""
        logger.info("Performing similarity search by vector with k=%d", k)

        search_req = SearchRequest.create(
            VectorSearch.from_vector_query(
                VectorQuery(
                    self.embedding_key,
                    query_embedding,
                    k,
                )
            )
        )

        fields = kwargs.get("fields", ["*"])

        if self.scoped_index:
            search_iter = self.scope.search(
                self.index_name,
                search_req,
                SearchOptions(
                    limit=k,
                    fields=fields,
                ),
            )
        else:
            search_iter = self.db_connection.search(
                index=self.index_name,
                request=search_req,
                options=SearchOptions(limit=k, fields=fields),
            )

        results = []
        for row in search_iter.rows():
            text = row.fields.pop(self.text_key, "")
            metadata = self._format_metadata(row.fields)
            score = row.score
            doc = VectorStoreDocument(
                id=row.id,
                text=text,
                vector=row.fields.get(self.embedding_key),
                attributes=metadata,
            )
            results.append(VectorStoreSearchResult(document=doc, score=score))

        logger.info("Found %d results in similarity search by vector", len(results))
        return results

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        # id_filter = ",".join([f"{id!s}" for id in include_ids])
        # logger.debug("Created filter by ID: %s", id_filter)
        # return f"search.in(id, '{id_filter}', ',')"

        raise NotImplementedError(
            "filter_by_id method is not implemented for CouchbaseVectorStore"
        )

    def _format_metadata(self, row_fields: dict[str, Any]) -> dict[str, Any]:
        """Format the metadata from the Couchbase Search API.

        Extract and reorganize metadata fields from the Couchbase Search API response.
        """
        metadata = {}
        for key, value in row_fields.items():
            if key.startswith("attributes."):
                new_key = key.split("attributes.")[-1]
                metadata[new_key] = value
            else:
                metadata[key] = value
        return metadata
