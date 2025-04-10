# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""
# %%
from datetime import datetime, timezone
from typing import cast
from uuid import uuid4
import logging
import numpy as np
import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.cluster_graph import cluster_graph
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.typing.context import PipelineRunContext, PipelineStorage
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.storage.file_pipeline_storage import FilePipelineStorage

from sklearn.cluster import DBSCAN
from graphrag.prompts.index.merge_entities import MERGE_ENTITIES_INPUT, MERGE_ENTITIES_SYSTEM

from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.language_model.manager import ModelManager
from graphrag.config.load_config import load_config, Path

from json_repair import loads
from json import dump

log = logging.getLogger(__name__)
# from graphrag.language_model.manager import ChatModel
from graphrag.config.embeddings import (
    entity_title_embedding,
    #get_embedded_fields,
    get_embedding_settings,
)
from graphrag.index.workflows.generate_text_embeddings import generate_text_embeddings


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:

    llm_config = config.models["default_chat_model"]
    llm = ModelManager().get_or_create_chat_model(
        name="extract_claims",
        model_type=llm_config.type,
        config=llm_config,
        callbacks=context.callbacks,
        cache=context.cache,
    )
    # Load entities and relationships
    entities = await load_table_from_storage("entities", context.storage)
    relationships = await load_table_from_storage("relationships", context.storage)

    if "human_readable_id" not in entities.columns:
        entities["human_readable_id"] = entities.index
    if "id" not in entities.columns:
        entities["id"] = entities["human_readable_id"].apply(lambda _x: str(uuid4()))
    # Embed entities.title
    embeddings_df = await create_entity_title_embedding(entities, config, context)
    embeddings_df = embeddings_df["entity.title"]

    # calculate cosine similarity
    embeddings_numpy = embeddings_df["embedding"].values
    embeddings_numpy = np.stack(embeddings_numpy, axis=0)
    similarity_matrix = cosine_similarity_matrix(embeddings_numpy)
    # clustering
    embeddings_df["cluster"] = get_dbscan_cluster_labels(similarity_matrix,eps = config.merge_entities.eps,min_samples = config.merge_entities.min_samples)
    # find duplicates
    llm_json = find_duplicate_entities(llm, embeddings_df, entities)
    
    with open(config.output.base_dir + '/merged_entities.json', 'w') as f:
        dump({"length": len(llm_json), "llm_json": llm_json}, f)
    # update
    entities, relationships = update_entities_relationships(
        entities, relationships, llm_json
    )
    
    # save
    await write_table_to_storage(relationships, "relationships", context.storage)
    await write_table_to_storage(entities, "entities", context.storage)

    return WorkflowFunctionOutput(
        result={
            "entities": entities,
            "relationships": relationships,
        }
    )


def find_duplicate_entities(llm, embeddings: pd.DataFrame, entities: pd.DataFrame):
    prompt_input = get_input_for_prompt(embeddings=embeddings, entities=entities)
    prompt = MERGE_ENTITIES_SYSTEM + MERGE_ENTITIES_INPUT.format(input=prompt_input)
    response = llm.chat(prompt).output.content
    llm_json = loads(response)
    return llm_json


async def create_entity_title_embedding(
    entities, config: GraphRagConfig, context: PipelineRunContext
):
    embedded_fields = set([entity_title_embedding])
    config_copy = config.copy()
    config_copy.embed_text.target = "selected"
    text_embed = get_embedding_settings(config_copy)

    # LANCEDB_URI = f"{config.root_dir}/output/lancedb"
    # embeddings_df = load_embeddings_from_default_entity_title(LANCEDB_URI)

    embeddings_df = await generate_text_embeddings(
        documents=None,
        relationships=None,
        text_units=None,
        community_reports=None,
        entities=entities,
        callbacks=context.callbacks,
        cache=context.cache,
        text_embed_config=text_embed,
        embedded_fields=embedded_fields,
    )

    return embeddings_df


def update_entities_relationships(entities: pd.DataFrame, relationships, response):
    import itertools

    entities = entities.set_index("human_readable_id", drop=False)
    entities.index = entities.index.astype(int)
    all_ids = []
    new_entities_list = []
    for item in response:
        """
        item is llm output
        {
        "ids": [4, 13],
        "entities": ["PCB", "PRINTED CIRCUIT BOARD"],
        "final_entity": "PRINTED CIRCUIT BOARD",
        "final_description": "A printed circuit board (PCB), also known as a printed wiring board (PWB) or printed board, is a thin board of insulating material used in electronics assembly to hold and connect electronic components. The PCB serves as a substrate, typically made from thermosetting or thermoplastic plastics, reinforced with materials like paper, glass fiber, cotton, or nylon. It features conductive pathways (usually copper) printed on one or both sides, which interconnect components via soldering to lands (pads). These connections are made either through plated through-holes for leaded components or directly onto the surface for surface-mount components. PCBs are manufactured using printing techniques, and the conductive tracks can be created additively (adding tracks) or subtractively (removing excess material from a pre-coated base). They are available in single-sided, double-sided, and multi-layered configurations, and are essential in all electronic assemblies, providing support and pathways for components during the soldering process.",
        "final_type": "MATERIAL"
        }
        """
        if len(item) < 1:
            continue
        
        try:
            item["ids"] = list(map(int, item["ids"]))
            old_rows = entities.loc[item["ids"], :]
            new_id = old_rows["id"].iloc[0]  # How to generate a new id? uuid?
            human_readable_id = old_rows.index[
                0
            ]  # How to generate a new human readable id? just autoincrement ?
            new_title = item["final_entity"]
            new_type = item["final_type"]
            new_description = item["final_description"]
            new_x = old_rows["x"].mean()  # How to generate a new x?
            new_y = old_rows[ "y"].mean()  # How to generate a new y? umap will be generated in the last workflow?
            frequency = old_rows["frequency"].sum()
            degree = old_rows["degree"].sum()
            textunit_ids = old_rows["text_unit_ids"]
            textunit_ids = list(itertools.chain.from_iterable(textunit_ids))
            row = {
                "id": new_id,
                "human_readable_id": human_readable_id,
                "title": new_title,
                "type": new_type,
                "description": new_description,
                "text_unit_ids": textunit_ids,
                "frequency": frequency,
                "degree": degree,
                "x": new_x,
                "y": new_y,
            }
            relationships.loc[
                relationships["source"].isin(item["entities"]), "source"
            ] = new_title
            relationships.loc[
                relationships["target"].isin(item["entities"]), "target"
            ] = new_title
            # Do we need to update relationships descriptions? I think yes but it may not be necessary
            #because we only merge close entities
            
            new_entities_list.append(row)
            all_ids.extend(item["ids"])
        except Exception as e:
            log.exception("update_entities_relationships: %s", e)
            

    """"
    or this version
        updated_source = relationships['source'].where(
        ~relationships['source'].isin(item['entities']), new_title
    )

    updated_target = relationships['target'].where(
        ~relationships['target'].isin(item['entities']), new_title
    )

    updated_relationships = relationships.assign(source=updated_source, target=updated_target)
        
    """
    entities = entities.drop(all_ids)
    entities = pd.concat([entities, pd.DataFrame(new_entities_list)])
    return entities, relationships


def cosine_similarity_matrix(X):
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    X_normalized = X / norms
    sim_matrix = np.dot(X_normalized, X_normalized.T)
    sim_matrix = np.clip(sim_matrix, -1.0, 1.0)
    return sim_matrix


def get_dbscan_cluster_labels(similarity_matrix,eps=0.2,min_samples=2):

    dbscan = DBSCAN(
        metric="precomputed", eps=eps, min_samples=min_samples
    )  # eps=0.2 corresponds to 80% similarity
    cosine_distance = 1 - similarity_matrix
    labels = dbscan.fit_predict(cosine_distance)
    return labels


def get_input_for_prompt(embeddings: pd.DataFrame, entities: pd.DataFrame):
    text = ""
    for cluster_id, group_df in embeddings.groupby("cluster"):
        if cluster_id == -1:
            continue
        row = entities.loc[
            group_df.index, ["human_readable_id", "title", "type", "description"]
        ]
        text += "cluster:" + str(cluster_id) + "\n"
        text += str(row.rename({"human_readable_id": "id"}).to_dict("records")) + "\n"

    return text
