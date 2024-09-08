import os
import pandas as pd

from graphrag.config.models.graphdb_config import GraphDBConfig
import numpy as np

import ast

from gremlin_python.driver import client, serializer
from azure.identity import ManagedIdentityCredential

import time
import os
import json

# Azure Cosmos DB Gremlin Endpoint and other constants
COSMOS_DB_SCOPE = "https://cosmos.azure.com/.default"  # The scope for Cosmos DB
class GraphDBClient:
    def __init__(self,graph_db_params: GraphDBConfig|None,context_id: str|None):
        self.username_prefix=graph_db_params.username
        token = f"{graph_db_params.account_key}"
        if(os.environ.get("ENVIRONMENT") == "AZURE"):
            credential = ManagedIdentityCredential(client_id="295ce65c-28c6-4763-be6f-a5eb36c3ceb3")
            token = credential.get_token(COSMOS_DB_SCOPE)
        self._client=client.Client(
            url=f"wss://{graph_db_params.account_name}.gremlin.cosmos.azure.com:443/",
            traversal_source="g",
            username=self.username_prefix+"-contextid-"+context_id,
            password=token",
            message_serializer=serializer.GraphSONSerializersV2d0(),
        )

    def result_to_df(self,result) -> pd.DataFrame:
        json_data = []
        for row in result:
            json_row = row[0]
            properties_dict = json_row.pop('properties')
            formatted_properties={}
            for k,v in properties_dict.items():
                new_val=v
                if isinstance(v,list) and isinstance(v[0],dict):
                    new_val=v[0]['value']
                if k=='description_embedding' or k =='text_unit_ids' or k=='graph_embedding':
                    new_val=ast.literal_eval(new_val)
                if isinstance(new_val,list):
                    new_val=np.array(new_val)
                formatted_properties[k]=new_val
            json_row.update(formatted_properties)
            json_data.append(json_row)
        df = pd.DataFrame(json_data)
        return df

    def query_vertices(self,context_id:str) -> pd.DataFrame:
        result = self._client.submit(
            message=(
                "g.V()"
            ),
        )
        return self.result_to_df(result)

    def query_edges(self,context_id:str) -> pd.DataFrame:
        result = self._client.submit(
            message=(
                "g.E()"
            ),
        )
        return self.result_to_df(result)

    def element_exists(self,element_type:str,element_id:int,conditions:str="")->bool:
        result=self._client.submit(
                message=(
                        element_type+
                        ".has('id',prop_id)"+
                        conditions+
                        ".count()"
                ),
                bindings={
                        "prop_id":element_id,
                }
        )
        element_count=0
        for counts in result:
            element_count=counts[0]
        return element_count>0

    def write_vertices(self,data: pd.DataFrame)->None:
        for row in data.itertuples():
            if self.element_exists("g.V()",row.id):
                continue
            else:
                self._client.submit(
                    message=(
                        "g.addV('entity')"
                        ".property('id', prop_id)"
                        ".property('name', prop_name)"
                        ".property('type', prop_type)"
                        ".property('description','prop_description')"
                        ".property('human_readable_id', prop_human_readable_id)"
                        ".property('category', prop_partition_key)"
                        ".property(list,'description_embedding',prop_description_embedding)"
                        ".property(list,'graph_embedding',prop_graph_embedding)"
                        ".property(list,'text_unit_ids',prop_text_unit_ids)"
                    ),
                    bindings={
                        "prop_id": row.id,
                        "prop_name": row.name,
                        "prop_type": row.type,
                        "prop_description": row.description,
                        "prop_human_readable_id": row.human_readable_id,
                        "prop_partition_key": "entities",
                        "prop_description_embedding":json.dumps(row.description_embedding.tolist() if row.description_embedding is not None else []),
                        "prop_graph_embedding":json.dumps(row.graph_embedding.tolist() if row.graph_embedding is not None else []),
                        "prop_text_unit_ids":json.dumps(row.text_unit_ids.tolist() if row.text_unit_ids is not None else []),
                    },
                )
            time.sleep(5)


    def write_edges(self,data: pd.DataFrame)->None:
        for row in data.itertuples():
            if self.element_exists("g.E()",row.id):
                continue
            self._client.submit(
                message=(
                    "g.V().has('name',prop_source_id)"
                    ".addE('connects')"
                    ".to(g.V().has('name',prop_target_id))"
                    ".property('weight',prop_weight)"
                    ".property(list,'text_unit_ids',prop_text_unit_ids)"
                    ".property('description',prop_description)"
                    ".property('id',prop_id)"
                    ".property('human_readable_id',prop_human_readable_id)"
                    ".property('source_degree',prop_source_degree)"
                    ".property('target_degree',prop_target_degree)"
                    ".property('rank',prop_rank)"
                    ".property('source',prop_source)"
                    ".property('target',prop_target)"
                ),
                bindings={
                    "prop_partition_key": "entities",
                    "prop_source_id": row.source,
                    "prop_target_id": row.target,
                    "prop_weight": row.weight,
                    "prop_text_unit_ids":json.dumps(row.text_unit_ids.tolist() if row.text_unit_ids is not None else []),
                    "prop_description": row.description,
                    "prop_id": row.id,
                    "prop_human_readable_id": row.human_readable_id,
                    "prop_source_degree": row.source_degree,
                    "prop_target_degree": row.target_degree,
                    "prop_rank": row.rank,
                    "prop_source": row.source,
                    "prop_target": row.target,
                },
            )
            time.sleep(5)