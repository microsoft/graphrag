# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import Any

from graphrag.data_model.entity import Entity
from graphrag.data_model.types import TextEmbedder
from graphrag.language_model.manager import ModelManager
from graphrag.query.context_builder.entity_extraction import (
    EntityVectorStoreKey,
    map_query_to_entities,
)
from graphrag.vector_stores.base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class MockBaseVectorStore(BaseVectorStore):
    def __init__(self, documents: list[VectorStoreDocument]) -> None:
        super().__init__("mock")
        self.documents = documents

    def connect(self, **kwargs: Any) -> None:
        raise NotImplementedError

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
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
                    document=document, score=abs(len(text) - len(document.text or ""))
                )
                for document in self.documents
            ],
            key=lambda x: x.score,
        )[:k]

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        return [document for document in self.documents if document.id in include_ids]

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
        text_embedding_vectorstore=MockBaseVectorStore([
            VectorStoreDocument(id=entity.id, text=entity.title, vector=None)
            for entity in entities
        ]),
        text_embedder=ModelManager().get_or_create_embedding_model(
            model_type="mock_embedding", name="mock"
        ),
        all_entities_dict={entity.id: entity for entity in entities},
        embedding_vectorstore_key=EntityVectorStoreKey.ID,
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
        query="t22",
        text_embedding_vectorstore=MockBaseVectorStore([
            VectorStoreDocument(id=entity.title, text=entity.title, vector=None)
            for entity in entities
        ]),
        text_embedder=ModelManager().get_or_create_embedding_model(
            model_type="mock_embedding", name="mock"
        ),
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
        text_embedding_vectorstore=MockBaseVectorStore([
            VectorStoreDocument(id=entity.id, text=entity.title, vector=None)
            for entity in entities
        ]),
        text_embedder=ModelManager().get_or_create_embedding_model(
            model_type="mock_embedding", name="mock"
        ),
        all_entities_dict={entity.id: entity for entity in entities},
        embedding_vectorstore_key=EntityVectorStoreKey.ID,
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

    assert map_query_to_entities(
        query="",
        text_embedding_vectorstore=MockBaseVectorStore([
            VectorStoreDocument(id=entity.id, text=entity.title, vector=None)
            for entity in entities
        ]),
        text_embedder=ModelManager().get_or_create_embedding_model(
            model_type="mock_embedding", name="mock"
        ),
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
