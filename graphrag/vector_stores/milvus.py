import json
from typing import Any
from graphrag.model.types import TextEmbedder
from graphrag.vector_stores import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)
from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, connections, utility


class MilvusDBVectorStore(BaseVectorStore):
    """The Milvus vector storage implementation."""

    def connect(self, **kwargs: Any) -> Any:

        db_uri = kwargs.get("db_uri", "http://localhost:19530")
        self.db_connection = connections.connect(uri=db_uri)

    def load_documents(
            self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:

        id_fields = []
        text_fields = []
        vector_fields = []
        attributes_fields = []
        for document in documents:
            if document.vector is not None:
                id_fields.append(document.id)
                text_fields.append(document.text)
                vector_fields.append(document.vector)
                attributes_fields.append(json.dumps(document.attributes))

        data = [id_fields, text_fields, vector_fields, attributes_fields]

        if len(data) == 0:
            data = None

        if overwrite:
            if data:
                self.create_collection()
                self.insert_data(data)
            else:
                self.create_collection()
        else:
            if data:
                self.insert_data(data)

    def create_collection(self) -> Collection:
        id_field = FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=128)
        text_field = FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=10240)
        vector_field = FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536)
        attributes_field = FieldSchema(name="attributes", dtype=DataType.VARCHAR, max_length=10240)

        schema = CollectionSchema(fields=[
            id_field,
            text_field,
            vector_field,
            attributes_field,
        ], description="GraphRAG Local Collection")

        collection = Collection(name=self.collection_name, schema=schema)
        return collection

    def delete_collection(self) -> None:
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)

    def insert_data(self, data) -> None:
        collection = Collection(name=self.collection_name)
        collection.insert(data)

        index_params = {
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
            "metric_type": "L2"
        }

        collection.create_index(field_name="vector", index_params=index_params)

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:

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

        collection = Collection(name=self.collection_name)
        collection.load()

        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }

        output_fields = [
            "text",
            "vector",
            "attributes"
        ]

        if self.query_filter:
            results = collection.search(data=[query_embedding],
                                        anns_field="vector",
                                        param=search_params,
                                        limit=k,
                                        output_fields=output_fields,
                                        expr=self.query_filter)
        else:
            results = collection.search(data=[query_embedding],
                                        anns_field="vector",
                                        param=search_params,
                                        output_fields=output_fields,
                                        limit=k)

        docs = []
        ids = []
        for result in results:
            for hit in result:

                text = hit.entity.get("text")
                vector = hit.entity.get("vector")
                attributes = hit.entity.get("attributes")

                ids.append({
                    "id": hit.id,
                    "text": text,
                    "distance": hit.distance,
                    "attributes": attributes,
                })

                docs.append(
                    VectorStoreSearchResult(
                        document=VectorStoreDocument(
                            id=hit.id,
                            text=text,
                            vector=vector,
                            attributes=json.loads(attributes),
                        ),
                        score=1 - abs(float(hit.distance)),
                    )
                )


        self.delete_collection()

        return docs

    def similarity_search_by_text(
            self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:

        query_embedding = text_embedder(text)

        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        return []
