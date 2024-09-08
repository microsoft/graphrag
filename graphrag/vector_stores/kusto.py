# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Azure Kusto vector storage implementation package."""
import os
import typing
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.helpers import dataframe_from_result_table
from graphrag.model.community_report import CommunityReport
from graphrag.model.entity import Entity
from graphrag.model.types import TextEmbedder

import pandas as pd
from pathlib import Path

import json
from typing import Any, List, cast

from graphrag.query.input.loaders.utils import (
    to_list,
    to_optional_dict,
    to_optional_float,
    to_optional_int,
    to_optional_list,
    to_optional_str,
    to_str,
)

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
        env = os.environ.get("ENVIRONMENT")
        if(env == "AZURE"):
            kcsb = KustoConnectionStringBuilder.with_aad_managed_service_identity_authentication(
                str(cluster), client_id="295ce65c-28c6-4763-be6f-a5eb36c3ceb3"
            )
        elif(env == "DEVELOPMENT"):
            kcsb = KustoConnectionStringBuilder.with_aad_device_authentication(str(cluster))
        else:
             kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
            str(cluster), str(client_id), str(client_secret), str(authority_id))
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
                "name": document.text,
                "vector": document.vector,
                "attributes": json.dumps(document.attributes),
            }
            for document in documents
            if document.vector is not None
        ]

        if len(data) == 0:
            return

        # Convert data to DataFrame
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
        Perform a vector-based similarity search. A search to find the k nearest neighbors of the given query vector.

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
        | extend similarity = series_cosine_similarity(query_vector, {self.vector_name})
        | top {k} by similarity desc
        """
        response = self.client.execute(self.database, query)
        df = dataframe_from_result_table(response.primary_results[0])
        print("Similarities of the search results:", [row["similarity"] for _, row in df.iterrows()])

        # Temporary to support the original entity_description_embedding
        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=row["id"],
                    text=row["text"],
                    vector=row[self.vector_name],
                    attributes=row["attributes"],
                ),
                score= 1 + float(row["similarity"]), # 1 + similarity to make it a score between 0 and 2
            )
            for _, row in df.iterrows()
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
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

    def get_extracted_entities(self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[Entity]:
        query_embedding = text_embedder(text)
        query = f"""
        let query_vector = dynamic({query_embedding});
        {self.collection_name}
        | extend similarity = series_cosine_similarity(query_vector, {self.vector_name})
        | top {k} by similarity desc
        """
        response = self.client.execute(self.database, query)
        df = dataframe_from_result_table(response.primary_results[0])

        return [
            Entity(
                id=row["id"],
                title=row["title"],
                type=row["type"],
                description=row["description"],
                graph_embedding=row["graph_embedding"],
                text_unit_ids=row["text_unit_ids"],
                description_embedding=row["description_embedding"],
                short_id="",
                community_ids=row["community_ids"],
                document_ids=row["document_ids"],
                rank=row["rank"],
                attributes=row["attributes"],
            ) for _, row in df.iterrows()
        ]

    def unload_entities(self) -> None:
        self.client.execute(self.database,f".drop table {self.collection_name} ifexists")

    def setup_entities(self) -> None:
        command = f".drop table {self.collection_name} ifexists"
        self.client.execute(self.database, command)
        command = f".create table {self.collection_name} (id: string, short_id: real, title: string, type: string, description: string, description_embedding: dynamic, name_embedding: dynamic, graph_embedding: dynamic, community_ids: dynamic, text_unit_ids: dynamic, document_ids: dynamic, rank: real, attributes: dynamic)"
        self.client.execute(self.database, command)
        command = f".alter column {self.collection_name}.graph_embedding policy encoding type = 'Vector16'"
        self.client.execute(self.database, command)
        command = f".alter column {self.collection_name}.description_embedding policy encoding type = 'Vector16'"
        self.client.execute(self.database, command)

    def load_entities(self, entities: list[Entity], overwrite: bool = False) -> None:
        # Convert data to DataFrame
        df = pd.DataFrame(entities)

        # Create or replace table
        if overwrite:
            self.setup_entities()

        # Ingest data
        ingestion_command = f".ingest inline into table {self.collection_name} <| {df.to_csv(index=False, header=False)}"
        self.client.execute(self.database, ingestion_command)

    def setup_reports(self) -> None:
        command = f".drop table {self.reports_name} ifexists"
        self.client.execute(self.database, command)
        command = f".create table {self.reports_name} (id: string, short_id: string, title: string, community_id: string, summary: string, full_content: string, rank: real, summary_embedding: dynamic, full_content_embedding: dynamic, attributes: dynamic)"
        self.client.execute(self.database, command)
        command = f".alter column {self.reports_name}.summary_embedding policy encoding type = 'Vector16'"
        self.client.execute(self.database, command)
        command = f".alter column {self.reports_name}.full_content_embedding policy encoding type = 'Vector16'"
        self.client.execute(self.database, command)

    def load_reports(self, reports: list[CommunityReport], overwrite: bool = False) -> None:
        # Convert data to DataFrame
        df = pd.DataFrame(reports)

        # Create or replace table
        if overwrite:
            self.setup_reports()

        # Ingest data
        ingestion_command = f".ingest inline into table {self.reports_name} <| {df.to_csv(index=False, header=False)}"
        self.client.execute(self.database, ingestion_command)


    def get_extracted_reports(
        self, community_ids: list[int], **kwargs: Any
    ) -> list[CommunityReport]:
        community_ids = ", ".join([str(id) for id in community_ids])
        query = f"""
        {self.reports_name}
        | where community_id in ({community_ids})
        """
        response = self.client.execute(self.database, query)
        df = dataframe_from_result_table(response.primary_results[0])

        return [
            CommunityReport(
                id=row["id"],
                short_id=row["short_id"],
                title=row["title"],
                community_id=row["community_id"],
                summary=row["summary"],
                full_content=row["full_content"],
                rank=row["rank"],
                summary_embedding=row["summary_embedding"],
                full_content_embedding=row["full_content_embedding"],
                attributes=row["attributes"],
            ) for _, row in df.iterrows()
        ]
