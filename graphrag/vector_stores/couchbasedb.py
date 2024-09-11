"""Couchbase vector store implementation for GraphRAG."""

import json
import logging
from typing import Any

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, SearchOptions
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
        scope_name: str,
        index_name: str,
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
        logger.debug(
            "Initialized CouchbaseVectorStore with collection: %s, bucket: %s, scope: %s, index: %s",
            collection_name, bucket_name, scope_name, index_name
        )

    def connect(self, **kwargs: Any) -> None:
        """Connect to the Couchbase vector store."""
        connection_string = kwargs.get("connection_string")
        username = kwargs.get("username")
        password = kwargs.get("password")

        if not isinstance(username, str) or not isinstance(password, str):
            error_msg = "Username and password must be strings"
            logger.error(error_msg)
            raise TypeError(error_msg)
        if not isinstance(connection_string, str):
            error_msg = "Connection string must be a string"
            logger.error(error_msg)
            raise TypeError(error_msg)

        logger.info("Connecting to Couchbase at %s", connection_string)
        auth = PasswordAuthenticator(username, password)
        options = ClusterOptions(auth)
        cluster = Cluster(connection_string, options)
        self.db_connection = cluster
        self.bucket = cluster.bucket(self.bucket_name)
        self.scope = self.bucket.scope(self.scope_name)
        self.document_collection = self.scope.collection(self.collection_name)
        logger.info("Successfully connected to Couchbase")

    def load_documents(self, documents: list[VectorStoreDocument]) -> None:
        """Load documents into vector storage."""
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
        if batch:
            try:
                result = self.document_collection.upsert_multi(batch)
                
                # Assuming the result has an 'all_ok' attribute
                if hasattr(result, "all_ok"):
                    if result.all_ok:
                        logger.info("Successfully loaded all %d documents", len(batch))
                    else:
                        logger.warning("Some documents failed to load")
                else:
                    logger.info("Unable to determine success status of document loading")
                
                # If there's a way to access individual results, log them
                if hasattr(result, "__iter__"):
                    for key, value in result:
                        logger.info("Document %s: %s", key, "Success" if value.success else "Failed")
                
            except Exception as e:
                logger.exception("Error occurred while loading documents: %s", str(e))
        else:
            logger.warning("No valid documents to load")

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
        id_filter = ",".join([f"{id!s}" for id in include_ids])
        logger.debug("Created filter by ID: %s", id_filter)
        return f"search.in(id, '{id_filter}', ',')"

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
