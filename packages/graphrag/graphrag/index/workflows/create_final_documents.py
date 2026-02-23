# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Workflow to create final documents with text unit mappings."""

import logging
from typing import Any

from graphrag_storage.tables.table import Table

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.row_transformers import (
    transform_document_row,
)
from graphrag.data_model.schemas import DOCUMENTS_FINAL_COLUMNS
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    _config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Transform final documents via streaming Table reads/writes."""
    logger.info("Workflow started: create_final_documents")

    async with (
        context.output_table_provider.open(
            "text_units",
        ) as text_units_table,
        context.output_table_provider.open(
            "documents",
            transformer=transform_document_row,
        ) as documents_table,
        context.output_table_provider.open(
            "documents",
        ) as output_table,
    ):
        sample = await create_final_documents(
            text_units_table,
            documents_table,
            output_table,
        )

    logger.info("Workflow completed: create_final_documents")
    return WorkflowFunctionOutput(result=sample)


async def create_final_documents(
    text_units_table: Table,
    documents_table: Table,
    output_table: Table,
) -> list[dict[str, Any]]:
    """Build text-unit mapping, then stream-enrich documents."""
    mapping: dict[str, list[str]] = {}
    async for row in text_units_table:
        document_id = row.get("document_id", "")
        if document_id:
            mapping.setdefault(document_id, []).append(
                row["id"],
            )

    sample_rows: list[dict[str, Any]] = []
    async for row in documents_table:
        row["text_unit_ids"] = mapping.get(row["id"], [])
        out = {c: row.get(c) for c in DOCUMENTS_FINAL_COLUMNS}
        await output_table.write(out)
        if len(sample_rows) < 5:
            sample_rows.append(out)

    return sample_rows
