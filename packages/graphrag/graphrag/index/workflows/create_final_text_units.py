# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from contextlib import nullcontext
from typing import Any

from graphrag_storage.tables.table import Table

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.row_transformers import (
    transform_entity_row,
    transform_relationship_row,
    transform_text_unit_row,
)
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

    has_covariates = (
        config.extract_claims.enabled
        and await context.output_table_provider.has("covariates")
    )
    # nullcontext() stands in when covariates are disabled so we can use
    # a single async with block regardless.
    cov_ctx = (
        context.output_table_provider.open("covariates")
        if has_covariates
        else nullcontext()
    )

    # Two separate handles for text_units: one for reading, one for
    # writing.  CSVTable reads directly from disk during iteration, so
    # writing through the same handle would truncate/corrupt the file
    # mid-read.  Separate handles keep the read and write paths isolated.
    async with (
        context.output_table_provider.open(
            "text_units",
            transformer=transform_text_unit_row,
        ) as text_units_table,
        context.output_table_provider.open(
            "entities",
            transformer=transform_entity_row,
        ) as entities_table,
        context.output_table_provider.open(
            "relationships",
            transformer=transform_relationship_row,
        ) as relationships_table,
        context.output_table_provider.open("text_units") as output_table,
        cov_ctx as covariates_table,
    ):
        sample = await create_final_text_units(
            text_units_table,
            entities_table,
            relationships_table,
            output_table,
            covariates_table,
        )

    logger.info("Workflow completed: create_final_text_units")
    return WorkflowFunctionOutput(result=sample)


async def create_final_text_units(
    text_units_table: Table,
    entities_table: Table,
    relationships_table: Table,
    output_table: Table,
    covariates_table: Table | None,
) -> list[dict[str, Any]]:
    """Enrich text units with entity, relationship, and covariate id lookups.

    Streams text units, looks up related ids from pre-built maps, writes
    each enriched row to output_table, and returns up to 5 sample rows.
    """
    entity_map = await _build_multi_ref_map(entities_table)
    relationship_map = await _build_multi_ref_map(relationships_table)
    covariate_map: dict[str, list[str]] = (
        await _build_covariate_map(covariates_table)
        if covariates_table is not None
        else {}
    )

    sample_rows: list[dict[str, Any]] = []
    human_readable_id = 0
    async for row in text_units_table:
        fields = {
            "id": row["id"],
            "human_readable_id": human_readable_id,
            "text": row["text"],
            "n_tokens": row["n_tokens"],
            "document_id": row["document_id"],
            "entity_ids": entity_map.get(row["id"], []),
            "relationship_ids": relationship_map.get(row["id"], []),
            "covariate_ids": covariate_map.get(row["id"], []),
        }
        out = {c: fields[c] for c in TEXT_UNITS_FINAL_COLUMNS}
        await output_table.write(out)
        if len(sample_rows) < 5:
            sample_rows.append(out)
        human_readable_id += 1

    return sample_rows


async def _build_multi_ref_map(table: Table) -> dict[str, list[str]]:
    """Build a text_unit_id -> [row_id] reverse lookup from a table with a text_unit_ids list field.

    Expects the table to have been opened with a transformer that
    already parsed ``text_unit_ids`` into a Python list.
    """
    result: dict[str, list[str]] = {}
    async for row in table:
        for tuid in row["text_unit_ids"]:
            result.setdefault(tuid, []).append(row["id"])
    return result


async def _build_covariate_map(table: Table) -> dict[str, list[str]]:
    """Build a text_unit_id -> [covariate_id] reverse lookup from the covariate table."""
    result: dict[str, list[str]] = {}
    async for row in table:
        result.setdefault(row["text_unit_id"], []).append(row["id"])
    return result
