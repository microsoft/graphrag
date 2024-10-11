import json
from typing import Any
import psycopg2
from graphrag.model.types import TextEmbedder
from graphrag.vector_stores import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class PgVectorStore(BaseVectorStore):
    """The PostgreSQL vector storage implementation."""

    def connect(self, **kwargs: Any) -> Any:

        dbname = kwargs.get("dbname", "postgres")
        user = kwargs.get("user", "postgres")
        password = kwargs.get("password", "")
        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", "5432")

        db_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }

        self.conn = psycopg2.connect(**db_params)
        self.cur = self.conn.cursor()

    def load_documents(
            self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:

        raws = []
        for document in documents:
            if document.vector is not None:
                raws.append({
                    "id": document.id,
                    "text": document.text,
                    "vector": document.vector,
                    "attributes": json.dumps(document.attributes)
                })

        if len(raws) == 0:
            raws = None

        if overwrite:
            if raws:
                self.create_pg_table()
                self.insert_data(raws)
            else:
                self.create_pg_table()
        else:
            if raws:
                self.insert_data(raws)

    def create_vector(self):
        try:
            sql = "CREATE EXTENSION vector;"
            self.cur.execute(sql)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

    def truncate_table(self):
        try:
            sql = f"TRUNCATE TABLE {self.collection_name};"
            self.cur.execute(sql)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

    def drop_pg_table(self):
        drop_table_query = f"drop table {self.collection_name};"

        try:
            self.cur.execute(drop_table_query)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def create_pg_table(self):
        create_table_query = f"""
CREATE TABLE IF NOT EXISTS {self.collection_name} (
    id VARCHAR(255) PRIMARY KEY,
    text TEXT,
    vector vector(1536),
    attributes TEXT
);
"""

        try:
            self.cur.execute(create_table_query)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def insert_raws(self, rows) -> None:
        query = f"INSERT INTO {self.collection_name} (id, text, vector, attributes) VALUES (%s, %s, %s, %s);"

        try:
            self.cur.executemany(query, rows)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def insert_data(self, raws) -> None:
        batch = []
        for raw in raws:
            current = (raw['id'], raw['text'], str(raw['vector']), raw['attributes'])
            if len(batch) < 100:
                batch.append(current)
            else:
                self.insert_raws(batch)
                batch = []

        if len(batch) > 0:
            self.insert_raws(batch)

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

        query = f"""
SELECT id, 
       vector, 
       text,
       attributes,
       vector <=> '{str(query_embedding)}' AS distance
FROM {self.collection_name}
ORDER BY distance
LIMIT {k};
        """
        self.cur.execute(query)

        results = self.cur.fetchall()

        docs = []
        ids = []
        for result in results:
            id = result[0]
            vector = result[1]
            text = result[2]
            attributes = result[3]
            distance = result[4]

            ids.append({
                "id": id,
                "text": text,
                "distance": distance,
                "attributes": attributes,
            })

            docs.append(
                VectorStoreSearchResult(
                    document=VectorStoreDocument(
                        id=id,
                        text=text,
                        vector=vector,
                        attributes=json.loads(attributes),
                    ),
                    score=1 - abs(float(distance)),
                )
            )

        self.drop_pg_table()

        return docs

    def similarity_search_by_text(
            self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:

        query_embedding = text_embedder(text)

        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        return []
