# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.schemas import TEXT_UNITS_FINAL_COLUMNS
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform the text units."""
    logger.info("Workflow started: create_final_text_units")
    
    # Check if covariates exist
    has_covariates = (
        config.extract_claims.enabled
        and await context.output_table_provider.has_dataframe("covariates")
    )
    
    # Use streaming approach
    await create_final_text_units_streaming(
        context.output_table_provider,
        has_covariates=has_covariates,
    )

    # Read back for return value to maintain workflow compatibility
    output = await context.output_table_provider.read_dataframe("text_units")
    logger.info("Workflow completed: create_final_text_units")
    return WorkflowFunctionOutput(result=output)


async def create_final_text_units_streaming(
    table_provider,
    has_covariates: bool = False,
) -> None:
    """Transform text units using streaming to reduce memory pressure."""
    from collections import defaultdict
    
    logger.info("Building lookup dictionaries from related tables...")
    
    # Build entity lookup: text_unit_id -> list[entity_id]
    entity_lookup = defaultdict(list)
    entities = await table_provider.read_dataframe("entities")
    for _, row in entities.iterrows():
        entity_id = row["id"]
        text_unit_ids = row.get("text_unit_ids", [])
        for tu_id in text_unit_ids:
            entity_lookup[tu_id].append(entity_id)
    
    logger.info("Built entity lookup with %d text units", len(entity_lookup))
    
    # Build relationship lookup: text_unit_id -> list[relationship_id]
    relationship_lookup = defaultdict(list)
    relationships = await table_provider.read_dataframe("relationships")
    for _, row in relationships.iterrows():
        rel_id = row["id"]
        text_unit_ids = row.get("text_unit_ids", [])
        for tu_id in text_unit_ids:
            relationship_lookup[tu_id].append(rel_id)
    
    logger.info("Built relationship lookup with %d text units", len(relationship_lookup))
    
    # Build covariate lookup if needed
    covariate_lookup = defaultdict(list)
    if has_covariates:
        covariates = await table_provider.read_dataframe("covariates")
        for _, row in covariates.iterrows():
            cov_id = row["id"]
            tu_id = row.get("text_unit_id")
            if tu_id:
                covariate_lookup[tu_id].append(cov_id)
        logger.info("Built covariate lookup with %d text units", len(covariate_lookup))
    
    logger.info("Streaming text units and attaching relationships...")
    
    # Stream over text_units, attach lookups, and write
    row_count = 0
    async with table_provider.open("text_units") as input_table:
        async with table_provider.open("text_units_temp") as output_table:
            for row in input_table:
                text_unit_id = row["id"]
                
                # Attach IDs from lookups
                row["entity_ids"] = entity_lookup.get(text_unit_id, [])
                row["relationship_ids"] = relationship_lookup.get(text_unit_id, [])
                row["covariate_ids"] = covariate_lookup.get(text_unit_id, [])
                
                await output_table.write(row)
                row_count += 1
                
                if row_count % 1000 == 0:
                    logger.info("Processed %d text units...", row_count)
    
    # Replace original with temp (read temp, delete old, write as original)
    temp_df = await table_provider.read_dataframe("text_units_temp")
    await table_provider.write_dataframe("text_units", temp_df)
    logger.info("Completed streaming %d text units", row_count)


def create_final_text_units(
    text_units: pd.DataFrame,
    final_entities: pd.DataFrame,
    final_relationships: pd.DataFrame,
    final_covariates: pd.DataFrame | None,
) -> pd.DataFrame:
    """All the steps to transform the text units."""
    selected = text_units.loc[:, ["id", "text", "document_id", "n_tokens"]]
    selected["human_readable_id"] = selected.index

    entity_join = _entities(final_entities)
    relationship_join = _relationships(final_relationships)

    entity_joined = _join(selected, entity_join)
    relationship_joined = _join(entity_joined, relationship_join)
    final_joined = relationship_joined

    if final_covariates is not None:
        covariate_join = _covariates(final_covariates)
        final_joined = _join(relationship_joined, covariate_join)
    else:
        final_joined["covariate_ids"] = [[] for i in range(len(final_joined))]

    aggregated = final_joined.groupby("id", sort=False).agg("first").reset_index()

    return aggregated.loc[
        :,
        TEXT_UNITS_FINAL_COLUMNS,
    ]


def _entities(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_ids"]]
    unrolled = selected.explode(["text_unit_ids"]).reset_index(drop=True)

    return (
        unrolled
        .groupby("text_unit_ids", sort=False)
        .agg(entity_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_ids": "id"})
    )


def _relationships(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_ids"]]
    unrolled = selected.explode(["text_unit_ids"]).reset_index(drop=True)

    return (
        unrolled
        .groupby("text_unit_ids", sort=False)
        .agg(relationship_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_ids": "id"})
    )


def _covariates(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_id"]]

    return (
        selected
        .groupby("text_unit_id", sort=False)
        .agg(covariate_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_id": "id"})
    )


def _join(left, right):
    return left.merge(
        right,
        on="id",
        how="left",
        suffixes=["_1", "_2"],
    )
