# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Azure Kusto vector storage implementation package."""

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.helpers import dataframe_from_result_table
from graphrag.model.types import TextEmbedder

import json
from typing import Any, List

from .base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class KustoVectorStore(BaseVectorStore):
    """The Azure Kusto vector storage implementation."""

    def connect(self, **kwargs: Any) -> Any:
        """
        Connect to the vector storage.

        Args:
            **kwargs: Arbitrary keyword arguments containing connection parameters.
                - cluster (str): The Kusto cluster URL.
                - database (str): The Kusto database name.
                - client_id (str): The client ID for AAD authentication.
                - client_secret (str): The client secret for AAD authentication.
                - authority_id (str): The authority ID (tenant ID) for AAD authentication.

        Returns:
            Any: The Kusto client instance.
        """
        cluster = kwargs.get("cluster")
        database = kwargs.get("database")
        client_id = kwargs.get("client_id")
        client_secret = kwargs.get("client_secret")
        authority_id = kwargs.get("authority_id")

        kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
            cluster, client_id, client_secret, authority_id
        )
        self.client = KustoClient(kcsb)
        self.database = database

    def load_documents(
        self, documents: List[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """
        Load documents into vector storage.

        Args:
            documents (List[VectorStoreDocument]): List of documents to be loaded.
            overwrite (bool): Whether to overwrite the existing table. Defaults to True.
        """
        data = [
            {
                "id": document.id,
                "text": document.text,
                "vector": document.vector,
                "attributes": json.dumps(document.attributes),
            }
            for document in documents
            if document.vector is not None
        ]

        if len(data) == 0:
            return

        # Convert data to DataFrame
        import pandas as pd
        df = pd.DataFrame(data)

        # Create or replace table
        if overwrite:
            command = f".drop table {self.collection_name} ifexists"
            self.client.execute(self.database, command)
            command = f".create table {self.collection_name} (id: string, text: string, vector: dynamic, attributes: string)"
            self.client.execute(self.database, command)

        # Ingest data
        ingestion_command = f".ingest inline into table {self.collection_name} <| {df.to_csv(index=False, header=False)}"
        self.client.execute(self.database, ingestion_command)

    def filter_by_id(self, include_ids: List[str] | List[int]) -> Any:
        """
        Build a query filter to filter documents by id.

        Args:
            include_ids (List[str] | List[int]): List of document IDs to include in the filter.

        Returns:
            Any: The query filter string.
        """
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
        self, query_embedding: List[float], k: int = 10, **kwargs: Any
    ) -> List[VectorStoreSearchResult]:
        """
        Perform a vector-based similarity search.

        Args:
            query_embedding (List[float]): The query embedding vector.
            k (int): The number of top results to return. Defaults to 10.
            **kwargs: Additional keyword arguments.

        Returns:
            List[VectorStoreSearchResult]: List of search results.
        """
        query = f"""
        let query_vector = dynamic({query_embedding});
        {self.collection_name}
        | extend distance = array_length(set_difference(vector, query_vector))
        | where distance <= {k}
        | top {k} by distance asc
        """
        response = self.client.execute(self.database, query)
        df = dataframe_from_result_table(response.primary_results[0])

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=row["id"],
                    text=row["text"],
                    vector=row["vector"],
                    attributes=json.loads(row["attributes"]),
                ),
                score=1 - abs(float(row["distance"])),
            )
            for _, row in df.iterrows()
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> List[VectorStoreSearchResult]:
        """
        Perform a similarity search using a given input text.

        Args:
            text (str): The input text to search for.
            text_embedder (TextEmbedder): The text embedder to convert text to vector.
            k (int): The number of top results to return. Defaults to 10.
            **kwargs: Additional keyword arguments.

        Returns:
            List[VectorStoreSearchResult]: List of search results.
        """
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        return []
