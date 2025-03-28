"""Local vector storage implementation."""

import json
import os
import gzip
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple
import math

import numpy as np
from scipy.spatial.distance import cosine

from graphrag.data_model.types import TextEmbedder
from graphrag.vector_stores.base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class LocalVectorStore(BaseVectorStore):
    """Local vector storage implementation using file system."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._data_dir: Path | None = None
        self._documents: Dict[str, VectorStoreDocument] = {}
        self._max_chunk_size: int = kwargs.get("max_chunk_size", 1000)
        self._compression_enabled: bool = kwargs.get("compression_enabled", False)
        self._vectors_loaded: bool = False
        self._doc_metadata: Dict[str, Dict[str, Any]] = {}
        
    def connect(self, **kwargs: Any) -> Any:
        """Connect to the local vector storage."""
        db_uri = kwargs.get("db_uri", "./data/vector_store")
        self._data_dir = Path(db_uri)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._max_chunk_size = kwargs.get("max_chunk_size", 1000)
        self._compression_enabled = kwargs.get("compression_enabled", False)
        self._load_existing_metadata()  # Load only metadata first

    def _get_metadata_path(self) -> Path:
        """Get path to metadata file."""
        if not self._data_dir:
            raise ValueError("Data directory not configured")
        return self._data_dir / f"{self.collection_name}_metadata.json"
    
    def _get_chunk_path(self, chunk_id: int) -> Path:
        """Get path to a specific chunk file."""
        if not self._data_dir:
            raise ValueError("Data directory not configured")
        filename = f"{self.collection_name}_chunk_{chunk_id}.json"
        if self._compression_enabled:
            filename += ".gz"
        return self._data_dir / filename
        
    def _load_existing_metadata(self) -> None:
        """Load existing metadata from disk."""
        metadata_path = self._get_metadata_path()
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                self._doc_metadata = metadata.get("documents", {})
                
    def _load_vectors_if_needed(self) -> None:
        """Load vectors from disk if not already loaded."""
        if self._vectors_loaded:
            return
            
        # First clear any existing documents (keeping metadata)
        self._documents.clear()
        
        # Load chunks
        chunk_id = 0
        while True:
            chunk_path = self._get_chunk_path(chunk_id)
            if not chunk_path.exists():
                break
                
            try:
                if self._compression_enabled:
                    with gzip.open(chunk_path, "rt", encoding="utf-8") as f:
                        chunk_data = json.load(f)
                else:
                    with open(chunk_path, "r", encoding="utf-8") as f:
                        chunk_data = json.load(f)
                        
                for doc_id, doc_data in chunk_data.items():
                    self._documents[doc_id] = VectorStoreDocument(
                        id=doc_id,
                        text=doc_data["text"],
                        vector=doc_data["vector"],
                        attributes=doc_data["attributes"],
                    )
            except Exception as e:
                print(f"Error loading chunk {chunk_id}: {e}")
                
            chunk_id += 1
            
        self._vectors_loaded = True

    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        if not self._data_dir:
            return
            
        metadata_path = self._get_metadata_path()
        metadata = {
            "collection_name": self.collection_name,
            "document_count": len(self._doc_metadata),
            "chunk_count": math.ceil(len(self._doc_metadata) / self._max_chunk_size),
            "documents": self._doc_metadata
        }
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _save_data(self) -> None:
        """Save data to disk in chunks."""
        if not self._data_dir:
            return
            
        # Update metadata
        self._doc_metadata = {
            doc_id: {
                "id": doc_id,
                "text_length": len(doc.text) if doc.text else 0,
                "attributes": doc.attributes
            }
            for doc_id, doc in self._documents.items()
        }
        
        # Save metadata
        self._save_metadata()
        
        # Chunk documents and save
        chunks = self._chunk_documents(self._documents, self._max_chunk_size)
        
        # First clear any existing chunks
        chunk_id = 0
        while True:
            chunk_path = self._get_chunk_path(chunk_id)
            if chunk_path.exists():
                chunk_path.unlink()
            else:
                break
            chunk_id += 1
            
        # Save new chunks
        for chunk_id, chunk_docs in enumerate(chunks):
            chunk_data = {
                doc_id: {
                    "text": doc.text,
                    "vector": doc.vector,
                    "attributes": doc.attributes,
                }
                for doc_id, doc in chunk_docs.items()
            }
            
            chunk_path = self._get_chunk_path(chunk_id)
            
            if self._compression_enabled:
                with gzip.open(chunk_path, "wt", encoding="utf-8") as f:
                    json.dump(chunk_data, f, ensure_ascii=False)
            else:
                with open(chunk_path, "w", encoding="utf-8") as f:
                    json.dump(chunk_data, f, ensure_ascii=False, indent=2)
                    
    def _chunk_documents(
        self, documents: Dict[str, VectorStoreDocument], chunk_size: int
    ) -> List[Dict[str, VectorStoreDocument]]:
        """Split documents into chunks of specified size."""
        if not documents:
            return []
            
        doc_items = list(documents.items())
        chunk_count = math.ceil(len(doc_items) / chunk_size)
        chunks = []
        
        for i in range(chunk_count):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(doc_items))
            chunk = dict(doc_items[start_idx:end_idx])
            chunks.append(chunk)
            
        return chunks

    def load_documents(
        self, documents: List[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into vector storage."""
        # Ensure vectors are loaded first
        self._load_vectors_if_needed()
        
        if overwrite:
            self._documents.clear()

        for doc in documents:
            if doc.vector is not None:
                self._documents[doc.id] = doc

        self._save_data()

    def load_documents_in_chunks(
        self, documents: List[VectorStoreDocument], chunk_size: int = 100, overwrite: bool = True
    ) -> None:
        """Load documents in chunks to handle large document sets.
        
        Args:
            documents: List of documents to load
            chunk_size: Size of each processing chunk
            overwrite: Whether to overwrite existing documents
        """
        # Ensure vectors are loaded if needed
        self._load_vectors_if_needed()
        
        if overwrite:
            self._documents.clear()
            
        # Process in chunks
        for i in range(0, len(documents), chunk_size):
            chunk = documents[i:i+chunk_size]
            
            for doc in chunk:
                if doc.vector is not None:
                    self._documents[doc.id] = doc
                    
            # Save periodically to avoid memory issues
            if (i + chunk_size) >= len(documents) or (i + chunk_size) % (chunk_size * 10) == 0:
                self._save_data()
                
    def filter_by_id(self, include_ids: List[str] | List[int]) -> Any:
        """Build a query filter to filter documents by id."""
        if not include_ids:
            self.query_filter = None
        else:
            self.query_filter = include_ids
        return self.query_filter
    
    def filter_by_attributes(self, attribute_filters: Dict[str, Any]) -> None:
        """Filter documents by attributes.
        
        Args:
            attribute_filters: Dictionary of attribute name and value to filter by
        """
        if not attribute_filters:
            self.query_filter = None
            return
            
        # Load metadata if needed
        if not self._doc_metadata:
            self._load_existing_metadata()
            
        # Find matching document IDs
        matching_ids = []
        for doc_id, metadata in self._doc_metadata.items():
            attributes = metadata.get("attributes", {})
            match = True
            
            for attr_name, attr_value in attribute_filters.items():
                if attr_name not in attributes or attributes[attr_name] != attr_value:
                    match = False
                    break
                    
            if match:
                matching_ids.append(doc_id)
                
        self.query_filter = matching_ids

    def _compute_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        return 1 - cosine(vec1, vec2)

    def similarity_search_by_vector(
        self, query_embedding: List[float], k: int = 10, **kwargs: Any
    ) -> List[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        # Ensure vectors are loaded
        self._load_vectors_if_needed()
        
        results = []
        for doc_id, doc in self._documents.items():
            if self.query_filter and doc_id not in self.query_filter:
                continue

            if doc.vector is not None:
                similarity = self._compute_similarity(query_embedding, doc.vector)
                results.append(
                    VectorStoreSearchResult(
                        document=doc,
                        score=similarity,
                    )
                )

        # Sort by similarity score and take top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> List[VectorStoreSearchResult]:
        """Perform a similarity search using a given input text."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        return []

    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        # First check if document exists in metadata
        if id not in self._doc_metadata and not self._vectors_loaded:
            # If not in metadata and vectors aren't loaded, we know it doesn't exist
            return VectorStoreDocument(id=id, text=None, vector=None)
            
        # Load vectors if needed
        self._load_vectors_if_needed()
        return self._documents.get(id, VectorStoreDocument(id=id, text=None, vector=None))
        
    def export_data(self, export_path: str = None) -> str:
        """Export all data to a JSON file.
        
        Args:
            export_path: Optional path for export file. If not provided, 
                        uses collection name in data directory.
                        
        Returns:
            Path to the exported file.
        """
        # Ensure vectors are loaded
        self._load_vectors_if_needed()
        
        if not export_path:
            if not self._data_dir:
                raise ValueError("No data directory configured")
            export_path = self._data_dir / f"{self.collection_name}_export.json"
        else:
            export_path = Path(export_path)
            
        export_data = {
            "collection_name": self.collection_name,
            "documents": [
                {
                    "id": doc.id,
                    "text": doc.text, 
                    "vector": doc.vector,
                    "attributes": doc.attributes
                }
                for doc in self._documents.values()
            ]
        }
        
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
        return str(export_path)
    
    def import_data(self, import_path: str, merge: bool = False) -> int:
        """Import data from a JSON file.
        
        Args:
            import_path: Path to the import file
            merge: If True, merge with existing data; if False, replace
            
        Returns:
            Number of documents imported
        """
        # Ensure vectors are loaded if doing a merge
        if merge:
            self._load_vectors_if_needed()
            
        import_path = Path(import_path)
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")
            
        with open(import_path, "r", encoding="utf-8") as f:
            import_data = json.load(f)
            
        if not merge:
            self._documents.clear()
            
        documents = []
        for doc_data in import_data.get("documents", []):
            doc = VectorStoreDocument(
                id=doc_data["id"],
                text=doc_data["text"],
                vector=doc_data["vector"],
                attributes=doc_data["attributes"]
            )
            documents.append(doc)
            
        # Use chunked loading for large imports
        self.load_documents_in_chunks(documents, chunk_size=self._max_chunk_size, overwrite=False)
        return len(documents)
    
    def get_document_count(self) -> int:
        """Get the total number of documents in the store."""
        # Use metadata if available
        if self._doc_metadata:
            return len(self._doc_metadata)
        else:
            # Fallback to loaded documents
            self._load_vectors_if_needed()
            return len(self._documents)
    
    def clear(self) -> None:
        """Clear all documents from the store."""
        self._documents.clear()
        self._doc_metadata.clear()
        self._save_data()
        
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        # Load metadata to ensure it's up to date
        self._load_existing_metadata()
        
        # Calculate disk usage
        disk_usage = 0
        metadata_path = self._get_metadata_path()
        if metadata_path.exists():
            disk_usage += metadata_path.stat().st_size
            
        chunk_id = 0
        while True:
            chunk_path = self._get_chunk_path(chunk_id)
            if chunk_path.exists():
                disk_usage += chunk_path.stat().st_size
                chunk_id += 1
            else:
                break
                
        return {
            "collection_name": self.collection_name,
            "document_count": len(self._doc_metadata),
            "disk_usage_bytes": disk_usage,
            "disk_usage_mb": round(disk_usage / (1024 * 1024), 2),
            "compression_enabled": self._compression_enabled,
            "chunk_count": chunk_id,
            "vectors_loaded": self._vectors_loaded
        } 