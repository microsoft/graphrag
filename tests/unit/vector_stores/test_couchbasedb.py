
import unittest
from unittest.mock import MagicMock, patch

from graphrag.model.types import VectorStoreDocument, VectorStoreSearchResult
from graphrag.vector_stores.couchbasedb import CouchbaseVectorStore


class TestCouchbaseVectorStore(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.vector_store = CouchbaseVectorStore(
            collection_name="test_collection",
            bucket_name="test_bucket",
            scope_name="test_scope",
            index_name="test_index"
        )
        self.vector_store.db_connection = MagicMock()
        self.vector_store.document_collection = MagicMock()
        self.vector_store.scope = MagicMock()

    async def test_connect(self):
        with patch('graphrag.vector_stores.couchbasedb.Cluster') as mock_cluster:
            self.vector_store.connect(
                connection_string="couchbase://localhost",
                username="test_user",
                password="test_password"
            )
            mock_cluster.assert_called_once()
            self.assertIsNotNone(self.vector_store.db_connection)

    async def test_load_documents(self):
        documents = [
            VectorStoreDocument(id="1", text="Test 1", vector=[0.1, 0.2, 0.3], attributes={"attr": "value1"}),
            VectorStoreDocument(id="2", text="Test 2", vector=[0.4, 0.5, 0.6], attributes={"attr": "value2"})
        ]
        self.vector_store.load_documents(documents)
        self.assertEqual(self.vector_store.document_collection.upsert.call_count, 2)

    async def test_similarity_search_by_text(self):
        mock_text_embedder = MagicMock(return_value=[0.1, 0.2, 0.3])
        with patch.object(self.vector_store, 'similarity_search_by_vector') as mock_search:
            mock_search.return_value = [
                VectorStoreSearchResult(
                    document=VectorStoreDocument(id="1", text="Test 1", vector=[0.1, 0.2, 0.3]),
                    score=0.9
                )
            ]
            results = self.vector_store.similarity_search_by_text("test query", mock_text_embedder, k=1)
            self.assertEqual(len(results), 1)
            mock_search.assert_called_once_with([0.1, 0.2, 0.3], 1)

    async def test_similarity_search_by_vector(self):
        mock_search_iter = MagicMock()
        mock_search_iter.rows.return_value = [
            MagicMock(id="1", fields={"text": "Test 1", "embedding": [0.1, 0.2, 0.3]}, score=0.9)
        ]
        self.vector_store.scope.search.return_value = mock_search_iter

        results = self.vector_store.similarity_search_by_vector([0.1, 0.2, 0.3], k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document.id, "1")
        self.assertEqual(results[0].document.text, "Test 1")
        self.assertEqual(results[0].score, 0.9)

    def test_filter_by_id(self):
        filter_query = self.vector_store.filter_by_id(["1", "2", "3"])
        self.assertEqual(filter_query, "search.in(id, '1,2,3', ',')")

    def test_format_metadata(self):
        row_fields = {
            "attributes.attr1": "value1",
            "attributes.attr2": "value2",
            "other_field": "other_value"
        }
        metadata = self.vector_store._format_metadata(row_fields)
        self.assertEqual(metadata, {
            "attr1": "value1",
            "attr2": "value2",
            "other_field": "other_value"
        })

if __name__ == '__main__':
    unittest.main()