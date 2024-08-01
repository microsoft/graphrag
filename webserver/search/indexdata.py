import os
from typing import Optional

import pandas as pd

from graphrag.model import Relationship, Covariate, Entity, CommunityReport, TextUnit
from graphrag.query.indexer_adapters import read_indexer_relationships, read_indexer_covariates, read_indexer_entities, \
    read_indexer_reports, read_indexer_text_units
from ..utils import consts


async def get_index_data(input_dir: str, datatype: str, id: Optional[int] = None):
    if datatype == "entities":
        return await get_entity(input_dir, id)
    elif datatype == "claims":
        return await get_claim(input_dir, id)
    elif datatype == "sources":
        return await get_source(input_dir, id)
    elif datatype == "reports":
        return await get_report(input_dir, id)
    elif datatype == "relationships":
        return await get_relationship(input_dir, id)
    else:
        raise ValueError(f"Unknown datatype: {datatype}")


async def get_entity(input_dir: str, row_id: Optional[int] = None) -> Entity:
    entity_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_TABLE}.parquet")
    entity_embedding_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet")

    entities = read_indexer_entities(entity_df, entity_embedding_df, consts.COMMUNITY_LEVEL)
    return entities[row_id]


async def get_claim(input_dir: str, row_id: Optional[int] = None) -> Covariate:
    covariate_file = f"{input_dir}/{consts.COVARIATE_TABLE}.parquet"
    if os.path.exists(covariate_file):
        covariate_df = pd.read_parquet(covariate_file)
        claims = read_indexer_covariates(covariate_df)
    else:
        raise ValueError(f"No claims {input_dir} of id {row_id} found")
    return claims[row_id]


async def get_source(input_dir: str, row_id: Optional[int] = None) -> TextUnit:
    text_unit_df = pd.read_parquet(f"{input_dir}/{consts.TEXT_UNIT_TABLE}.parquet")
    text_units = read_indexer_text_units(text_unit_df)
    return text_units[row_id]


async def get_report(input_dir: str, row_id: Optional[int] = None) -> CommunityReport:
    entity_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_TABLE}.parquet")
    report_df = pd.read_parquet(f"{input_dir}/{consts.COMMUNITY_REPORT_TABLE}.parquet")
    reports = read_indexer_reports(report_df, entity_df, consts.COMMUNITY_LEVEL)
    return reports[row_id]


async def get_relationship(input_dir: str, row_id: Optional[int] = None) -> Relationship:
    relationship_df = pd.read_parquet(f"{input_dir}/{consts.RELATIONSHIP_TABLE}.parquet")
    relationships = read_indexer_relationships(relationship_df)
    return relationships[row_id]
