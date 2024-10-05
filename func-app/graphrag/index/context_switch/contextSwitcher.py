import asyncio
import os
from io import BytesIO
from pathlib import Path
from typing import cast

import pandas as pd

from common.graph_db_client import GraphDBClient
from graphrag.common.progress import ProgressReporter
from graphrag.common.storage import (
    BlobPipelineStorage,
    FilePipelineStorage,
    PipelineStorage,
)
from graphrag.common.utils.context_utils import get_files_by_contextid
from graphrag.config import (
    GraphRagConfig,
    create_graphrag_config,
)
from graphrag.config.enums import StorageType
from graphrag.model.community_report import CommunityReport
from graphrag.model import TextUnit
from graphrag.model.entity import Entity
from graphrag.query.indexer_adapters import (
    read_indexer_entities,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.model.entity import Entity
from azure.cosmos import CosmosClient, PartitionKey
from graphrag.vector_stores.base import BaseVectorStore
from graphrag.vector_stores.typing import VectorStoreFactory, VectorStoreType
import logging

class ContextSwitcher:
    """ContextSwitcher class definition."""

    def __init__(self, root_dir:str , config_dir:str,reporter: ProgressReporter,
                 context_id:str, community_level:int ,
                 data_dir: str = None,
                 optimized_search: bool= False,
                 use_kusto_community_reports: bool = False,):

        self.root_dir=root_dir
        self.config_dir=config_dir
        self.data_dir=data_dir
        self.reporter=reporter
        self.context_id=context_id
        self.optimized_search=optimized_search
        self.community_level = community_level
        self.use_kusto_community_reports = use_kusto_community_reports
        logging.info("ContextSwitcher initialized")

    def get_embedding_store(self,config_args):
        """Set up the vector store and return it."""
        if not config_args:
            config_args = {}

        collection_name = config_args.get(
            "query_collection_name", "entity_description_embeddings"
        )

        collection_name += "_" + self.context_id
        config_args.update({"collection_name": collection_name})

        vector_name = config_args.get(
            "vector_search_column", "description_embedding"
        )
        config_args.update({"vector_name": vector_name})
        config_args.update({"reports_name": f"reports_{self.context_id}"})


        config_args.update({"text_units_name": f"text_units_{self.context_id}"})

        return VectorStoreFactory.get_vector_store(
            vector_store_type=VectorStoreType.Kusto, kwargs=config_args
        )



    def setup_vector_store(self,
            config_args: dict | None = None,) -> BaseVectorStore:

        description_embedding_store = self.get_embedding_store(config_args)
        description_embedding_store.connect(**config_args)

        description_embedding_store.setup_entities()
        if self.use_kusto_community_reports:
            description_embedding_store.setup_reports()

        description_embedding_store.setup_text_units()

        return description_embedding_store

    def _read_config_parameters(self,root: str, config: str | None):
        reporter=self.reporter
        _root = Path(root)
        settings_yaml = (
            Path(config)
            if config and Path(config).suffix in [".yaml", ".yml"]
            else _root / "settings/settings.yaml"
        )
        if not settings_yaml.exists():
            settings_yaml = _root / "settings/settings.yml"

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
            else _root / "settings/settings.json"
        )
        if settings_json.exists():
            reporter.info(f"Reading settings from {settings_json}")
            with settings_json.open("rb") as file:
                import json

                data = json.loads(file.read().decode(encoding="utf-8", errors="strict"))
                return create_graphrag_config(data, root)

        reporter.info("Reading settings from environment variables")
        return create_graphrag_config(root_dir=root)

    def activate(self, files:[str]=[]):
        """Activate the context."""
        #1. read the context id to fileId mapping.
        #2. read the file from storage using common/blob_storage_client.py
        #3. GraphDB: use cosmos db client to load data into Cosmos DB.
        #4. KustoDB: use Kusto client to load embedding data into Kusto.
        data_dir=self.data_dir
        root_dir=self.root_dir
        config_dir=self.config_dir
        reporter=self.reporter
        context_id=self.context_id
        optimized_search=self.optimized_search
        community_level=self.community_level

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
                data_dir = root_dir #_infer_data_dir(cast(str, root_dir))
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
            return self._read_config_parameters(root or "./", config_dir)

        ################################################################################


        _, _, config = _configure_paths_and_settings(
            data_dir, root_dir, config_dir
        )

        if(config.storage.type == StorageType.memory):
            ValueError("Memory storage is not supported")
        if(config.storage.type == StorageType.blob):
            if(config.storage.container_name is not None):
                input_storage_client: PipelineStorage = BlobPipelineStorage(connection_string=config.storage.connection_string, container_name=config.storage.container_name, storage_account_blob_url=config.storage.storage_account_blob_url)
            else:
                ValueError("Storage type is Blob but container name is invalid")
        if(config.storage.type == StorageType.file):
            input_storage_client: PipelineStorage = FilePipelineStorage(config.root_dir)

        data_paths = []
        if(len(files) > 0):
            logging.info("Using files passed from query")
            data_paths=files
        else:
            logging.info("reading files from settings files")
            data_paths = get_files_by_contextid(config, context_id)
        final_nodes = pd.DataFrame()
        final_community_reports = pd.DataFrame()
        final_text_units = pd.DataFrame()
        final_relationships = pd.DataFrame()
        final_entities = pd.DataFrame()
        final_covariates = pd.DataFrame()
        graph_db_client=None

        if config.graphdb.enabled:
            cosmos_client = CosmosClient(
                f"{config.graphdb.cosmos_url}",
                f"{config.graphdb.account_key}",
            )
            database_name = config.graphdb.username.split("/")[2]
            database = cosmos_client.get_database_client(database_name)
            graph_name=config.graphdb.username.split("/")[-1]+"-contextid-"+context_id
            graph = database.create_container_if_not_exists(
                id=graph_name,
                partition_key=PartitionKey(path='/category'),
                offer_throughput=400
            )
            graph_db_client = GraphDBClient(config.graphdb,context_id)

        description_embedding_store = self.setup_vector_store(config_args=config.embeddings.vector_store)

        added_vertices = set()
        for data_path in data_paths:
            #check from the config for the ouptut storage type and then read the data from the storage.

            #GraphDB: we may need to make change below to read nodes data from Graph DB
            final_nodes = read_paraquet_file(input_storage_client, data_path + "/create_final_nodes.parquet")
            final_community_reports = read_paraquet_file(input_storage_client, data_path + "/create_final_community_reports.parquet") # KustoDB: Final_entities, Final_Nodes, Final_report should be merged and inserted to kusto
            final_text_units = read_paraquet_file(input_storage_client, data_path + "/create_final_text_units.parquet") # lance db search need it for embedding mapping. we have embeddings in entities we should use from there. KustoDB already must have sorted it.

            if not optimized_search:
                final_covariates = read_paraquet_file(input_storage_client, data_path + "/create_final_covariates.parquet")

            final_relationships = read_paraquet_file(input_storage_client, data_path + "/create_final_relationships.parquet")
            final_entities = read_paraquet_file(input_storage_client, data_path + "/create_final_entities.parquet")

            vector_store_args = (
                config.embeddings.vector_store if config.embeddings.vector_store else {}
            )

            reporter.info(f"Vector Store Args: {vector_store_args}")

            if "type" not in vector_store_args:
                ValueError("vectore_store.type can't be empty")

            vector_store_type = vector_store_args.get("type")

            if vector_store_type != VectorStoreType.Kusto:
                ValueError("Context switching is only supporeted for vectore_store.type=kusto ")

            entities = read_indexer_entities(final_nodes, final_entities, community_level) # KustoDB: read Final nodes data and entities data and merge it.
            reports = read_indexer_reports(final_community_reports, final_nodes, community_level)
            text_units = read_indexer_text_units(final_text_units)

            description_embedding_store.load_entities(entities)
            if self.use_kusto_community_reports:
                raise ValueError("Community reports not supported for kusto.")
                #description_embedding_store.load_reports(reports)

            description_embedding_store.load_text_units(text_units)

            if config.graphdb.enabled:
                graph_db_client.write_vertices(final_entities, added_vertices)
                graph_db_client.write_edges(final_relationships)

        if config.graphdb.enabled:
            graph_db_client._client.close()

    def deactivate(self):
        """DeActivate the context."""

        config=self._read_config_parameters(self.root_dir or "./",self.config_dir)
        config_args = config.embeddings.vector_store
        description_embedding_store = self.get_embedding_store(config_args)
        description_embedding_store.connect(**config_args)
        description_embedding_store.unload_entities()

        if config.graphdb.enabled:
            g_client=GraphDBClient(config.graphdb,self.context_id)
            g_client.remove_graph()