# write kusto db here.
import lancedb as lancedb  # noqa: I001 (Ruff was breaking on this file imports, even tho they were sorted and passed local tests)
from graphrag.model.types import TextEmbedder
from typing import Any

from .base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)
class KustoDBVectorStore(BaseVectorStore):
    """Kusto vector store."""
    
    def __init__(self, **kwargs):
        """Initialize the Kusto vector store."""
        pass

    def connect(self, **kwargs: Any) -> Any:
        """Connect to the vector storage."""
        pass

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into vector storage."""
        pass

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        pass

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        return []
    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a similarity search using a given input text."""
        return []
