# Constants for Couchbase connection
import os
import time
import unittest

from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions
from dotenv import load_dotenv

from graphrag.vector_stores.base import VectorStoreDocument, VectorStoreSearchResult
from graphrag.vector_stores.couchbasedb import CouchbaseVectorStore

load_dotenv()

COUCHBASE_CONNECTION_STRING = os.getenv(
    "COUCHBASE_CONNECTION_STRING", "couchbase://localhost"
)
COUCHBASE_USERNAME = os.getenv("COUCHBASE_USERNAME", "Administrator")
COUCHBASE_PASSWORD = os.getenv("COUCHBASE_PASSWORD", "password")
BUCKET_NAME = os.getenv("COUCHBASE_BUCKET_NAME", "graphrag-demo")
SCOPE_NAME = os.getenv("COUCHBASE_SCOPE_NAME", "shared")
COLLECTION_NAME = os.getenv(
    "COUCHBASE_COLLECTION_NAME", "entity_description_embeddings"
)
INDEX_NAME = os.getenv("COUCHBASE_INDEX_NAME", "graphrag_index")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 1536))


class TestCouchbaseVectorStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vector_store = CouchbaseVectorStore(
            collection_name=COLLECTION_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            index_name=INDEX_NAME,
            vector_size=VECTOR_SIZE,
        )
        auth = PasswordAuthenticator(COUCHBASE_USERNAME, COUCHBASE_PASSWORD)
        cluster_options = ClusterOptions(auth)

        cls.vector_store.connect(
            connection_string=COUCHBASE_CONNECTION_STRING,
            cluster_options=cluster_options,
        )

    @classmethod
    def tearDownClass(cls):
        # Clean up the test collection
        query = f"DELETE FROM `{BUCKET_NAME}`.`{SCOPE_NAME}`.`{COLLECTION_NAME}`"
        cls.vector_store.db_connection.query(query).execute()

    def test_load_documents(self):
        documents = [
            VectorStoreDocument(
                id="1",
                text="Test 1",
                vector=[0.1] * VECTOR_SIZE,
                attributes={"attr": "value1"},
            ),
            VectorStoreDocument(
                id="2",
                text="Test 2",
                vector=[0.2] * VECTOR_SIZE,
                attributes={"attr": "value2"},
            ),
        ]
        self.vector_store.load_documents(documents)

        # Add a sleep to allow time for indexing
        time.sleep(2)

        # Verify documents were loaded
        for doc in documents:
            result = self.vector_store.document_collection.get(doc.id)
            assert result.content_as[dict] is not None
            assert result.content_as[dict]["text"] == doc.text

    def test_similarity_search_by_vector(self):
        # Ensure we have some documents in the store
        self.test_load_documents()

        # Add a sleep to allow time for indexing
        time.sleep(2)

        results = self.vector_store.similarity_search_by_vector(
            [0.1] * VECTOR_SIZE, k=2
        )
        assert len(results) == 2
        assert isinstance(results[0], VectorStoreSearchResult)
        assert isinstance(results[0].document, VectorStoreDocument)

    def test_similarity_search_by_text(self):
        # Mock text embedder function
        def mock_text_embedder(text):
            return [0.1] * VECTOR_SIZE

        # Ensure we have some documents in the store
        self.test_load_documents()

        # Add a sleep to allow time for indexing
        time.sleep(2)

        results = self.vector_store.similarity_search_by_text(
            "test query", mock_text_embedder, k=2
        )
        assert len(results) == 2
        assert isinstance(results[0], VectorStoreSearchResult)
        assert isinstance(results[0].document, VectorStoreDocument)

    # def test_filter_by_id(self):
    #     filter_query = self.vector_store.filter_by_id(["1", "2", "3"])
    #     assert filter_query == "search.in(id, '1,2,3', ',')"


if __name__ == "__main__":
    unittest.main()
