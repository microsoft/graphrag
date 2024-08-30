from graphrag.common.progress import ProgressReporter
from graphrag.config import GraphRagConfig
from graphrag.config.enums import StorageType
from graphrag.common.storage import PipelineStorage, BlobPipelineStorage, FilePipelineStorage
from graphrag.common.utils.context_utils import get_files_by_contextid
import pandas as pd
from typing import cast
from azure.core.exceptions import ResourceNotFoundError
import asyncio
from io import BytesIO
from pathlib import Path
from graphrag.config import (
    create_graphrag_config,
    GraphRagConfig,
)
from common.graph_db_client import GraphDBClient
import os
from graphrag.vector_stores import VectorStoreFactory, VectorStoreType
from graphrag.vector_stores.base import BaseVectorStore
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.vector_stores.kusto import KustoVectorStore
from graphrag.query.indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    kt_read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.model.entity import Entity

class ContextSwitcher:
    """ContextSwitcher class definition."""

    def __init__(self, root_dir:str , config_dir:str,reporter: ProgressReporter,
                 context_id:str, community_level:int ,
                 data_dir: str = None,
                 optimized_search: bool= False):

        self.root_dir=root_dir
        self.config_dir=config_dir
        self.data_dir=data_dir
        self.reporter=reporter
        self.context_id=context_id
        self.optimized_search=optimized_search
        self.community_level = community_level

    def set_ctx_activation(
            self,
            activate: int,
            entities: list[Entity]=[],
            config_args: dict | None = None,
        ):
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

        description_embedding_store = VectorStoreFactory.get_vector_store(
                vector_store_type=VectorStoreType.Kusto, kwargs=config_args
        )
        description_embedding_store.connect(**config_args)

        if activate:
            description_embedding_store.load_entities(entities)
        else:
            description_embedding_store.unload_entities()

        return 0

    def activate(self):
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



        ################################################################################


        _, _, config = _configure_paths_and_settings(
            data_dir, root_dir, config_dir
        )

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
            graph_db_client = GraphDBClient(config.graphdb)
        for data_path in data_paths:
            #check from the config for the ouptut storage type and then read the data from the storage.

            #GraphDB: we may need to make change below to read nodes data from Graph DB
            final_nodes = pd.concat([final_nodes, read_paraquet_file(input_storage_client, data_path + "/create_final_nodes.parquet")])
            final_community_reports = pd.concat([final_community_reports,read_paraquet_file(input_storage_client, data_path + "/create_final_community_reports.parquet")]) # KustoDB: Final_entities, Final_Nodes, Final_report should be merged and inserted to kusto
            final_text_units = pd.concat([final_text_units, read_paraquet_file(input_storage_client, data_path + "/create_final_text_units.parquet")]) # lance db search need it for embedding mapping. we have embeddings in entities we should use from there. KustoDB already must have sorted it.

            if not optimized_search:
                final_covariates = pd.concat([final_covariates, read_paraquet_file(input_storage_client, data_path + "/create_final_covariates.parquet")])

            if config.graphdb.enabled:
                final_relationships = pd.concat([final_relationships, graph_db_client.query_edges()])
                final_entities = pd.concat([final_entities, graph_db_client.query_vertices()])
            else:
                final_relationships = pd.concat([final_relationships, read_paraquet_file(input_storage_client, data_path + "/create_final_relationships.parquet")])
                final_entities = pd.concat([final_entities, read_paraquet_file(input_storage_client, data_path + "/create_final_entities.parquet")])


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

            self.set_ctx_activation(
                entities=entities,
                activate=1, config_args=vector_store_args,
            )


    def deactivate(self):
        """DeActivate the context."""
        #1. Delete all the data for a given context id.
        self.set_ctx_activation(0)