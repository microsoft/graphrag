# Constants for Couchbase connection
import os
import unittest

from graphrag.vector_stores.base import VectorStoreDocument, VectorStoreSearchResult
from graphrag.vector_stores.couchbasedb import CouchbaseVectorStore

COUCHBASE_CONNECTION_STRING = os.environ.get("COUCHBASE_CONNECTION_STRING", "couchbase://localhost")
COUCHBASE_USERNAME = os.environ.get("COUCHBASE_USERNAME", "")
COUCHBASE_PASSWORD = os.environ.get("COUCHBASE_PASSWORD", "")
BUCKET_NAME = os.environ.get("COUCHBASE_BUCKET_NAME", "graphrag-demo")
SCOPE_NAME = os.environ.get("COUCHBASE_SCOPE_NAME", "shared")
COLLECTION_NAME = os.environ.get("COUCHBASE_COLLECTION_NAME", "entity_description_embeddings")
INDEX_NAME = os.environ.get("COUCHBASE_INDEX_NAME", "graphrag_index")


class TestCouchbaseVectorStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vector_store = CouchbaseVectorStore(
            collection_name=COLLECTION_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            index_name=INDEX_NAME
        )
        cls.vector_store.connect(
            connection_string=COUCHBASE_CONNECTION_STRING,
            username=COUCHBASE_USERNAME,
            password=COUCHBASE_PASSWORD
        )

    @classmethod
    def tearDownClass(cls):
        # Clean up the test collection
        query = f"DELETE FROM `{BUCKET_NAME}`.`{SCOPE_NAME}`.`{COLLECTION_NAME}`"
        cls.vector_store.db_connection.query(query).execute()

    def test_load_documents(self):
        documents = [
            VectorStoreDocument(id="1", text="Test 1", vector=[0.1, 0.2, 0.3], attributes={"attr": "value1"}),
            VectorStoreDocument(id="2", text="Test 2", vector=[0.4, 0.5, 0.6], attributes={"attr": "value2"})
        ]
        self.vector_store.load_documents(documents)

        # Verify documents were loaded
        for doc in documents:
            result = self.vector_store.document_collection.get(doc.id)
            assert result.content_as[dict] is not None
            assert result.content_as[dict]["text"] == doc.text

    def test_similarity_search_by_vector(self):
        # Ensure we have some documents in the store
        self.test_load_documents()

        results = self.vector_store.similarity_search_by_vector([0.1, 0.2, 0.3], k=2)
        assert len(results) == 2
        assert isinstance(results[0], VectorStoreSearchResult)
        assert isinstance(results[0].document, VectorStoreDocument)

    def test_similarity_search_by_text(self):
        # Mock text embedder function
        def mock_text_embedder(text):
            return [0.1, 0.2, 0.3]

        results = self.vector_store.similarity_search_by_text("test query", mock_text_embedder, k=2)
        assert len(results) == 2
        assert isinstance(results[0], VectorStoreSearchResult)
        assert isinstance(results[0].document, VectorStoreDocument)

    def test_filter_by_id(self):
        filter_query = self.vector_store.filter_by_id(["1", "2", "3"])
        assert filter_query == "search.in(id, '1,2,3', ',')"

if __name__ == "__main__":
    unittest.main()