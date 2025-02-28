# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.schemas import TEXT_UNITS_FINAL_COLUMNS
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import (
    load_table_from_storage,
    storage_has_table,
    write_table_to_storage,
)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform the text units."""
    text_units = await load_table_from_storage("text_units", context.storage)
    final_entities = await load_table_from_storage("entities", context.storage)
    final_relationships = await load_table_from_storage(
        "relationships", context.storage
    )
    final_covariates = None
    if config.extract_claims.enabled and await storage_has_table(
        "covariates", context.storage
    ):
        final_covariates = await load_table_from_storage("covariates", context.storage)

    output = create_final_text_units(
        text_units,
        final_entities,
        final_relationships,
        final_covariates,
    )

    await write_table_to_storage(output, "text_units", context.storage)

    return WorkflowFunctionOutput(result=output)


def create_final_text_units(
    text_units: pd.DataFrame,
    final_entities: pd.DataFrame,
    final_relationships: pd.DataFrame,
    final_covariates: pd.DataFrame | None,
) -> pd.DataFrame:
    """All the steps to transform the text units."""
    selected = text_units.loc[:, ["id", "text", "document_ids", "n_tokens"]]
    selected["human_readable_id"] = selected.index + 1

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
        unrolled.groupby("text_unit_ids", sort=False)
        .agg(entity_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_ids": "id"})
    )


def _relationships(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_ids"]]
    unrolled = selected.explode(["text_unit_ids"]).reset_index(drop=True)

    return (
        unrolled.groupby("text_unit_ids", sort=False)
        .agg(relationship_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_ids": "id"})
    )


def _covariates(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_id"]]

    return (
        selected.groupby("text_unit_id", sort=False)
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
