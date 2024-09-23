# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""GraphDBEmitter module."""

import pandas as pd
from common.graph_db_client import GraphDBClient
from .table_emitter import TableEmitter
from graphrag.config.models.graphdb_config import GraphDBConfig

class GraphDBEmitter(TableEmitter):
    """Graph DB Emitter."""

    def __init__(self, graph_db_params: GraphDBConfig|None,context_id: str|None):
        self.graph_db_client = GraphDBClient(graph_db_params,context_id)
        self.allowed_workflows = ['create_final_entities','create_final_relationships']

    async def emit(self, name: str, data: pd.DataFrame) -> None:
        if name not in self.allowed_workflows:
            return
        if name == 'create_final_entities':
            self.graph_db_client.write_vertices(data)
        if name == 'create_final_relationships':
            self.graph_db_client.write_edges(data)