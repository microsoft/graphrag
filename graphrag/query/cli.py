# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the query module."""

import os
from pathlib import Path
from typing import cast
from io import BytesIO
from graphrag.common.utils.context_utils import get_files_by_contextid
from graphrag.config.enums import StorageType
from azure.core.exceptions import ResourceNotFoundError

import pandas as pd

from graphrag.config import (
    create_graphrag_config,
    GraphRagConfig,
)
from graphrag.index.progress import PrintProgressReporter
from graphrag.model.entity import Entity
from graphrag.query.input.loaders.dfs import (
    store_entity_semantic_embeddings,
)
from graphrag.vector_stores import VectorStoreFactory, VectorStoreType
from graphrag.vector_stores.base import BaseVectorStore
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.vector_stores.kusto import KustoVectorStore
from graphrag.common.blob_storage_client import BlobStorageClient

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
    entities: list[Entity],
    vector_store_type: str = VectorStoreType.LanceDB,
    config_args: dict | None = None,
):
    """Get the embedding description store."""
    if not config_args:
        config_args = {}

    collection_name = config_args.get(
        "query_collection_name", "entity_description_embeddings"
    )
    config_args.update({"collection_name": collection_name})
    description_embedding_store = VectorStoreFactory.get_vector_store(
        vector_store_type=vector_store_type, kwargs=config_args
    )

    description_embedding_store.connect(**config_args)

    if config_args.get("overwrite", True):
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
):
    """Run a local search with the given query."""
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )

    data_paths = []
    data_paths = get_files_by_contextid(config, context_id)
    #data_paths = [Path("E:\\graphrag\\ragtest6\\output\\AtoG\\artifacts")]
    #data_paths = [Path("E:\\graphrag\\auditlogstest\\output\\securityPlatformPPE\\artifacts"),Path("E:\\graphrag\\auditlogstest\\output\\UnifiedFeedbackPPE\\artifacts")]
    #data_paths.append(Path(data_dir))
    final_nodes = pd.DataFrame()
    final_community_reports = pd.DataFrame()
    final_text_units = pd.DataFrame()
    final_relationships = pd.DataFrame()
    final_entities = pd.DataFrame()
    final_covariates = pd.DataFrame()
    if config.graphdb.enabled:
        graph_db_client = GraphDBClient(config.graphdb)
    for data_path in data_paths:
        #check from the config for the ouptut storage type and then read the data from the storage.
        
        #GraphDB: we may need to make change below to read nodes data from Graph DB
        final_nodes = pd.concat([final_nodes, read_paraquet_file(config, data_path + "/create_final_nodes.parquet", config.storage.type)])
        
        final_community_reports = pd.concat([final_community_reports,read_paraquet_file(config, data_path + "/create_final_community_reports.parquet", config.storage.type)])
        
        final_text_units = pd.concat([final_text_units, read_paraquet_file(config, data_path + "/create_final_text_units.parquet", config.storage.type)])
        
        if config.graphdb.enabled:
            final_relationships = pd.concat([final_relationships, graph_db_client.query_edges()])
            final_entities = pd.concat([final_entities, graph_db_client.query_vertices()])
        else:
            final_relationships = pd.concat([final_relationships, read_paraquet_file(config, data_path + "/create_final_relationships.parquet", config.storage.type)])
            final_entities = pd.concat([final_entities, read_paraquet_file(config, data_path + "/create_final_entities.parquet", config.storage.type)])

        data_path_object = Path(data_path)
        final_covariates_path = data_path_object / "create_final_covariates.parquet"

        final_covariates = pd.concat([final_covariates, (
            read_paraquet_file(config, final_covariates_path, config.storage.type) if final_covariates_path.exists() else None
        )])

    vector_store_args = (
        config.embeddings.vector_store if config.embeddings.vector_store else {}
    )

    reporter.info(f"Vector Store Args: {vector_store_args}")
    vector_store_type = vector_store_args.get("type", VectorStoreType.LanceDB) # verify kusto vector store here.

    entities = read_indexer_entities(final_nodes, final_entities, community_level) # Change it to read file specific indexer files.
    description_embedding_store = __get_embedding_description_store(
        entities=entities,
        vector_store_type=vector_store_type,
        config_args=vector_store_args,
    )
    covariates = (
        read_indexer_covariates(final_covariates)
        if final_covariates.empty is False
        else []
    )

    search_engine = get_local_search_engine(
        config,
        reports=read_indexer_reports(
            final_community_reports, final_nodes, community_level
        ),
        text_units=read_indexer_text_units(final_text_units),
        entities=entities,
        relationships=read_indexer_relationships(final_relationships),
        covariates={"claims": covariates},
        description_embedding_store=description_embedding_store,
        response_type=response_type,
    )

    result = search_engine.search(query=query)
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


def read_paraquet_file(config:GraphRagConfig, path: str, storageType: StorageType):
    #create different enum for paraquet storage type
    if storageType == StorageType.blob:
        container_name = config.input.container_name or ""
        blobStorageClient = BlobStorageClient(connection_string=config.input.connection_string, container_name=container_name, encoding="utf-8")
        container_client = blobStorageClient.get_container_client()
        if blob_exists(container_client, path):
            blob_data = container_client.download_blob(blob=path)
            bytes_io = BytesIO(blob_data.readall())
            return pd.read_parquet(bytes_io, engine="pyarrow")
        else:
            return pd.DataFrame() # return empty data frame as covariates file doesn't exist
    else:
        file_path = Path(path)
        if not file_path.exists():
            return pd.DataFrame()
        return pd.read_parquet(path)
# TODO I split this out for now to preserve how the original local search worked.
# I don't think this will necessarily be permanently separate.
# It was just easier without having to keep everything generic and work the same way as local search worked.
# One last optimization: Once all the merges are done we can go back to the parquet loads and optimize those for only the fields we need and merge them right away into one big table (I think).
def run_content_store_local_search(
    config_dir: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    query: str,
):
    """Run a local search with the given query."""
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )
    data_path = Path(data_dir)

    vector_store_args = (
        config.embeddings.vector_store if config.embeddings.vector_store else {}
    )
    
    vector_store_type = vector_store_args.get("type", VectorStoreType.Kusto)
    
    collection_name = vector_store_args.get(
        "query_collection_name", "entity_description_embeddings"
    )
    vector_store_args.update({"collection_name": collection_name})

    description_embedding_store = VectorStoreFactory.get_vector_store(
        vector_store_type=vector_store_type, kwargs=vector_store_args
    )

    description_embedding_store.connect(**vector_store_args)

    #TODO add back covariates. I skipped this for now.
    description_embedding_store.load_parqs(data_dir, ["create_final_nodes", "create_final_community_reports", "create_final_text_units", "create_final_relationships", "create_final_entities"])

    #TODO KQLify this. This merge of nodes & entities needs to happen in Kusto.
    create_entities_table(description_embedding_store, community_level)
    # description_embedding_store = __get_embedding_description_store(
    #     entities=entities,
    #     description_embedding_store=description_embedding_store,
    #     config_args=vector_store_args,
    # )

    #TODO add back covariates w/Kusto. I skipped this for now.
    # covariates = (
    #     read_indexer_covariates(final_covariates)
    #     if final_covariates is not None
    #     else []
    # )

    reports_result=kt_read_indexer_reports( description_embedding_store, community_level)

    #TODO KQLify this. I know at least the read_indedxer_reports needs to be done in Kusto. We are joining the community reports & final nodes.
    # search_engine = get_local_search_engine(
    #     config,
    #     reports=read_indexer_reports(
    #         final_community_reports, final_nodes, community_level
    #     ),
    #     text_units=read_indexer_text_units(final_text_units),
    #     entities=entities,
    #     relationships=read_indexer_relationships(final_relationships),
    #     covariates={"claims": covariates},
    #     description_embedding_store=description_embedding_store,
    #     response_type=response_type,
    # )

    #TODO This is the biggest TODO. I need to go through the whole mixed_context.py and make sure it's using Kusto data not the parquet data it expects in memory.
    # result = search_engine.search(query=query)
    # reporter.success(f"Local Search Response: {result.response}")
    # return result.response

    return True #Obviously this is a placeholder due to all the TODOs above.

# Create entities table similar to read_indexer_entities, but creating that table in Kusto, not in memory.
def create_entities_table(description_embedding_store: BaseVectorStore, community_level: int):
    description_embedding_store.execute_query(".set-or-replace entities <| ( \
    create_final_nodes | where level <= 2 | project name=['title'] ,rank=degree,community | \
    summarize community=max(community) by name,rank | join kind=inner \
    create_final_entities on name | project id,title=name,text=description,vector=description_embeddings)")

    '''
    description_embedding_store.execute_query(f".set entities <| create_final_nodes \
        | where level <= {community_level} \
        | project community=coalesce(community, 0), name=['title'], rank=degree \
        | summarize community=max(community) by name, rank \
        | join kind=inner create_final_entities on name")
    '''

def run_content_store_global_search(
    config_dir: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    query: str,
):
    """Run a content store global search with the given query."""
    raise NotImplementedError("This function is not implemented yet.")



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
