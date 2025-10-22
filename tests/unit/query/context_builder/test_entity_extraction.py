# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import Any

from graphrag.data_model.entity import Entity
from graphrag.query.context_builder.entity_extraction import (
    EntityVectorStoreKey,
    map_query_to_entities,
)
from graphrag_llm.config import LLMProviderType, ModelConfig
from graphrag_llm.embedding import create_embedding
from graphrag_vectors import (
    TextEmbedder,
    VectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)

embedding_model = create_embedding(
    ModelConfig(
        type=LLMProviderType.MockLLM,
        model_provider="openai",
        model="text-embedding-3-small",
        mock_responses=[1.0, 1.0, 1.0],
    )
)


class MockVectorStore(VectorStore):
    def __init__(self, documents: list[VectorStoreDocument]) -> None:
        super().__init__(index_name="mock")
        self.documents = documents

    def connect(self, **kwargs: Any) -> None:
        raise NotImplementedError

    def create_index(self) -> None:
        raise NotImplementedError

    def load_documents(self, documents: list[VectorStoreDocument]) -> None:
        raise NotImplementedError

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        return [
            VectorStoreSearchResult(document=document, score=1)
            for document in self.documents[:k]
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        return sorted(
            [
                VectorStoreSearchResult(
                    document=document,
                    score=abs(len(text) - len(str(document.id) or "")),
                )
                for document in self.documents
            ],
            key=lambda x: x.score,
        )[:k]

    def search_by_id(self, id: str) -> VectorStoreDocument:
        result = self.documents[0]
        result.id = id
        return result


def test_map_query_to_entities():
    entities = [
        Entity(
            id="2da37c7a-50a8-44d4-aa2c-fd401e19976c",
            short_id="sid1",
            title="t1",
            rank=2,
        ),
        Entity(
            id="c4f93564-4507-4ee4-b102-98add401a965",
            short_id="sid2",
            title="t22",
            rank=4,
        ),
        Entity(
            id="7c6f2bc9-47c9-4453-93a3-d2e174a02cd9",
            short_id="sid3",
            title="t333",
            rank=1,
        ),
        Entity(
            id="8fd6d72a-8e9d-4183-8a97-c38bcc971c83",
            short_id="sid4",
            title="t4444",
            rank=3,
        ),
    ]

    assert map_query_to_entities(
        query="t22",
        text_embedding_vectorstore=MockVectorStore([
            VectorStoreDocument(id=entity.title, vector=None) for entity in entities
        ]),
        text_embedder=embedding_model,
        all_entities_dict={entity.id: entity for entity in entities},
        embedding_vectorstore_key=EntityVectorStoreKey.TITLE,
        k=1,
        oversample_scaler=1,
    ) == [
        Entity(
            id="c4f93564-4507-4ee4-b102-98add401a965",
            short_id="sid2",
            title="t22",
            rank=4,
        )
    ]

    assert map_query_to_entities(
        query="",
        text_embedding_vectorstore=MockVectorStore([
            VectorStoreDocument(id=entity.id, vector=None) for entity in entities
        ]),
        text_embedder=embedding_model,
        all_entities_dict={entity.id: entity for entity in entities},
        embedding_vectorstore_key=EntityVectorStoreKey.TITLE,
        k=2,
    ) == [
        Entity(
            id="c4f93564-4507-4ee4-b102-98add401a965",
            short_id="sid2",
            title="t22",
            rank=4,
        ),
        Entity(
            id="8fd6d72a-8e9d-4183-8a97-c38bcc971c83",
            short_id="sid4",
            title="t4444",
            rank=3,
        ),
    ]
