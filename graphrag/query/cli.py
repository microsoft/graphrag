# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the query module."""

import asyncio
import os
from pathlib import Path
from typing import cast
from io import BytesIO
from graphrag.common.storage import PipelineStorage, BlobPipelineStorage, FilePipelineStorage
from graphrag.common.utils.context_utils import get_files_by_contextid
from graphrag.config.enums import StorageType
from azure.core.exceptions import ResourceNotFoundError

import pandas as pd

from graphrag.config import (
    create_graphrag_config,
    GraphRagConfig,
)
from graphrag.common.progress import PrintProgressReporter
from graphrag.model.entity import Entity
from graphrag.query.input.loaders.dfs import (
    store_entity_semantic_embeddings,
)
from graphrag.vector_stores import VectorStoreFactory, VectorStoreType
from graphrag.vector_stores.base import BaseVectorStore
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.vector_stores.kusto import KustoVectorStore
from .factories import get_global_search_engine, get_local_search_engine
from .indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    kt_read_indexer_reports,
    read_indexer_text_units,
)

from common.graph_db_client import GraphDBClient

reporter = PrintProgressReporter("")

reporter = PrintProgressReporter("")

def __get_embedding_description_store(
    entities: list[Entity] = [],
    vector_store_type: str = VectorStoreType.LanceDB,
    config_args: dict | None = None,
    context_id: str = "",
):
    """Get the embedding description store."""
    if not config_args:
        config_args = {}

    collection_name = config_args.get(
        "query_collection_name", "entity_description_embeddings"
    )
    config_args.update({"collection_name": f"{collection_name}_{context_id}" if context_id else collection_name})
    vector_name = config_args.get(
        "vector_search_column", "description_embedding"
    )
    config_args.update({"vector_name": vector_name})
    config_args.update({"reports_name": f"reports_{context_id}" if context_id else "reports"})

    description_embedding_store = VectorStoreFactory.get_vector_store(
        vector_store_type=vector_store_type, kwargs=config_args
    )

    description_embedding_store.connect(**config_args)

    if vector_store_type == VectorStoreType.Kusto:
        return description_embedding_store

    elif config_args.get("overwrite", True):
        # this step assumps the embeddings where originally stored in a file rather
        # than a vector database

        # dump embeddings from the entities list to the description_embedding_store
        store_entity_semantic_embeddings(
            entities=entities, vectorstore=description_embedding_store
        )
    else:
        # load description embeddings to an in-memory lancedb vectorstore
        # to connect to a remote db, specify url and port values.
        description_embedding_store = LanceDBVectorStore(
            collection_name=collection_name
        )
        description_embedding_store.connect(
            db_uri=config_args.get("db_uri", "./lancedb")
        )

        # load data from an existing table
        description_embedding_store.document_collection = (
            description_embedding_store.db_connection.open_table(
                description_embedding_store.collection_name
            )
        )

    return description_embedding_store


def run_global_search(
    config_dir: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    context_id: str,
    query: str,
):
    """Run a global search with the given query."""
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )
    if config.graphdb.enabled:
        graph_db_client = GraphDBClient(config.graphdb)
    data_path = Path(data_dir)

    final_nodes: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_nodes.parquet"
    )
    if config.graphdb.enabled:
        final_entities = graph_db_client.query_vertices()
    else:
        final_entities: pd.DataFrame = pd.read_parquet(
            data_path / "create_final_entities.parquet"
        )
    final_community_reports: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_community_reports.parquet"
    )

    reports = read_indexer_reports(
        final_community_reports, final_nodes, community_level
    )
    entities = read_indexer_entities(final_nodes, final_entities, community_level)
    search_engine = get_global_search_engine(
        config,
        reports=reports,
        entities=entities,
        response_type=response_type,
    )

    result = search_engine.search(query=query)

    reporter.success(f"Global Search Response: {result.response}")
    return result.response


def run_local_search(
    config_dir: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    context_id: str,
    query: str,
    optimized_search: bool = False,
    use_kusto_community_reports: bool = False,
):
    """Run a local search with the given query."""
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )

    # TODO: loading stage here must be only limited to default lancedb.

    # for the POC purpose input artifacts blob, output artifacts blob and input query blob storage are going to same.
    if(config.storage.type == StorageType.memory):
        ValueError("Memory storage is not supported")
    if(config.storage.type == StorageType.blob):
        if(config.storage.container_name is not None):
            input_storage_client: PipelineStorage = BlobPipelineStorage(config.storage.connection_string, config.storage.container_name)
            output_storage_client: PipelineStorage = BlobPipelineStorage(config.storage.connection_string, config.storage.container_name)
        else:
            ValueError("Storage type is Blob but container name is invalid")
    if(config.storage.type == StorageType.file):
        input_storage_client: PipelineStorage = FilePipelineStorage(config.root_dir)
        output_storage_client: PipelineStorage = FilePipelineStorage(config.root_dir)

    data_paths = []
    data_paths = get_files_by_contextid(config, context_id)
    final_nodes = pd.DataFrame()
    final_community_reports = pd.DataFrame()
    final_text_units = pd.DataFrame()
    final_relationships = pd.DataFrame()
    final_entities = pd.DataFrame()
    final_covariates = pd.DataFrame()
    if config.graphdb.enabled:
        graph_db_client = GraphDBClient(config.graphdb,context_id)
    for data_path in data_paths:
        #check from the config for the ouptut storage type and then read the data from the storage.

        #GraphDB: we may need to make change below to read nodes data from Graph DB
        final_nodes = pd.concat([final_nodes, read_paraquet_file(input_storage_client, data_path + "/create_final_nodes.parquet")])
        final_community_reports = pd.concat([final_community_reports,read_paraquet_file(input_storage_client, data_path + "/create_final_community_reports.parquet")]) # KustoDB: Final_entities, Final_Nodes, Final_report should be merged and inserted to kusto
        final_text_units = pd.concat([final_text_units, read_paraquet_file(input_storage_client, data_path + "/create_final_text_units.parquet")]) # lance db search need it for embedding mapping. we have embeddings in entities we should use from there. KustoDB already must have sorted it.

        if not optimized_search:
            final_covariates = pd.concat([final_covariates, read_paraquet_file(input_storage_client, data_path + "/create_final_covariates.parquet")])

        if config.graphdb.enabled:
            final_entities = pd.concat([final_entities, graph_db_client.query_vertices(context_id)])
            graph_db_client._client.close()
        else:
            final_entities = pd.concat([final_entities, read_paraquet_file(input_storage_client, data_path + "/create_final_entities.parquet")])

    
    vector_store_args = (
        config.embeddings.vector_store if config.embeddings.vector_store else {}
    )

    reporter.info(f"Vector Store Args: {vector_store_args}")
    vector_store_type = vector_store_args.get("type", VectorStoreType.LanceDB)

    entities = read_indexer_entities(final_nodes, final_entities, community_level) # KustoDB: read Final nodes data and entities data and merge it.
    reports=read_indexer_reports(
        final_community_reports, final_nodes, community_level
    )
    description_embedding_store = __get_embedding_description_store(
        entities=entities,
        vector_store_type=vector_store_type,
        config_args=vector_store_args,
        context_id=context_id,
    )

    covariates = (
        read_indexer_covariates(final_covariates)
        if final_covariates.empty is False
        else []
    )

    if(isinstance(description_embedding_store, KustoVectorStore)):
        entities = []
        if use_kusto_community_reports:
            reports = []

    search_engine = get_local_search_engine(
        config,
        reports=reports,
        text_units=read_indexer_text_units(final_text_units),
        entities=entities,
        relationships=[],
        covariates={"claims": covariates},
        description_embedding_store=description_embedding_store,
        response_type=response_type,
        context_id=context_id,
        is_optimized_search=optimized_search,
        use_kusto_community_reports=use_kusto_community_reports,
        graphdb_config=config.graphdb,
    )

    if optimized_search:
        result = search_engine.optimized_search(query=query)
    else:
        result = search_engine.search(query=query)
    for key in  result.context_data.keys():
        asyncio.run(output_storage_client.set("query/output/"+ key +".paraquet", result.context_data[key].to_parquet())) #it shows as error in editor but not an error.
    reporter.success(f"Local Search Response: {result.response}")
    return result.response

def blob_exists(container_client, blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    try:
        # Attempt to get the blob properties
        blob_client.get_blob_properties()
        return True
    except ResourceNotFoundError:
        # Blob does not exist
        return False


def read_paraquet_file(storage: PipelineStorage, path: str):
    #create different enum for paraquet storage type
    file_data = asyncio.run(storage.get(path, True))
    if file_data is None:
        return pd.DataFrame()
    return pd.read_parquet(BytesIO(file_data), engine="pyarrow")

def _configure_paths_and_settings(
    data_dir: str | None,
    root_dir: str | None,
    config_dir: str | None,
) -> tuple[str, str | None, GraphRagConfig]:
    if data_dir is None and root_dir is None:
        msg = "Either data_dir or root_dir must be provided."
        raise ValueError(msg)
    if data_dir is None:
        data_dir = _infer_data_dir(cast(str, root_dir))
    config = _create_graphrag_config(root_dir, config_dir)
    return data_dir, root_dir, config


def _infer_data_dir(root: str) -> str:
    output = Path(root) / "output"
    # use the latest data-run folder
    if output.exists():
        folders = sorted(output.iterdir(), key=os.path.getmtime, reverse=True)
        if len(folders) > 0:
            folder = folders[0]
            return str((folder / "artifacts").absolute())
    msg = f"Could not infer data directory from root={root}"
    raise ValueError(msg)


def _create_graphrag_config(
    root: str | None,
    config_dir: str | None,
) -> GraphRagConfig:
    """Create a GraphRag configuration."""
    return _read_config_parameters(root or "./", config_dir)


def _read_config_parameters(root: str, config: str | None):
    _root = Path(root)
    settings_yaml = (
        Path(config)
        if config and Path(config).suffix in [".yaml", ".yml"]
        else _root / "settings.yaml"
    )
    if not settings_yaml.exists():
        settings_yaml = _root / "settings.yml"

    if settings_yaml.exists():
        reporter.info(f"Reading settings from {settings_yaml}")
        with settings_yaml.open(
            "rb",
        ) as file:
            import yaml

            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    settings_json = (
        Path(config)
        if config and Path(config).suffix == ".json"
        else _root / "settings.json"
    )
    if settings_json.exists():
        reporter.info(f"Reading settings from {settings_json}")
        with settings_json.open("rb") as file:
            import json

            data = json.loads(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    reporter.info("Reading settings from environment variables")
    return create_graphrag_config(root_dir=root)
