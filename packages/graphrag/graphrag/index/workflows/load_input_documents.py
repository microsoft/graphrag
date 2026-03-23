# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from graphrag_input import InputReader, create_input_reader
from graphrag_storage.tables.table import Table

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.utils.hashing import gen_sha512_hash

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Load and parse input documents into a standard format."""
    input_reader = create_input_reader(config.input, context.input_storage)

    async with (
        context.output_table_provider.open("documents") as documents_table,
    ):
        sample, total_count = await load_input_documents(input_reader, documents_table)

        if total_count == 0:
            msg = "Error reading documents, please see logs."
            logger.error(msg)
            raise ValueError(msg)

        logger.info("Final # of rows loaded: %s", total_count)
        context.stats.num_documents = total_count

    return WorkflowFunctionOutput(result=sample)


async def load_input_documents(
    input_reader: InputReader, documents_table: Table, sample_size: int = 5
) -> tuple[pd.DataFrame, int]:
    """Load and parse input documents into a standard format."""
    sample: list[dict] = []
    idx = 0
    turn_counters: dict[str, int] = {}

    async for doc in input_reader:
        row = asdict(doc)
        row["human_readable_id"] = idx
        if "raw_data" not in row:
            row["raw_data"] = None
        normalize_conversation_metadata(row, turn_counters)
        await documents_table.write(row)
        if len(sample) < sample_size:
            sample.append(row)
        idx += 1

    return pd.DataFrame(sample), idx


def normalize_conversation_metadata(
    row: dict[str, Any], turn_counters: dict[str, int] | None = None
) -> dict[str, Any]:
    """Normalize optional conversation metadata on a documents row."""
    counters = turn_counters if turn_counters is not None else {}

    conversation_id = row.get("conversation_id")
    if _is_missing_value(conversation_id):
        source_identifier = _get_source_identifier(row)
        conversation_id = gen_sha512_hash({"seed": source_identifier}, ["seed"])
    row["conversation_id"] = conversation_id

    turn_index = row.get("turn_index")
    if _is_missing_value(turn_index):
        turn_index = counters.get(conversation_id, 0)
        counters[conversation_id] = turn_index + 1
    else:
        next_turn_index = _parse_turn_index(turn_index)
        counters[conversation_id] = max(
            counters.get(conversation_id, 0),
            next_turn_index + 1,
        )
    row["turn_index"] = turn_index

    turn_timestamp = row.get("turn_timestamp")
    if _is_missing_value(turn_timestamp):
        creation_date = row.get("creation_date")
        turn_timestamp = (
            creation_date
            if not _is_missing_value(creation_date)
            else datetime.now(timezone.utc).isoformat()
        )
    row["turn_timestamp"] = turn_timestamp

    turn_role = row.get("turn_role")
    if _is_missing_value(turn_role):
        turn_role = "unknown"
    row["turn_role"] = turn_role
    return row


def _get_source_identifier(row: dict[str, Any]) -> str:
    raw_data = row.get("raw_data") if isinstance(row.get("raw_data"), dict) else {}
    title = row.get("title") or raw_data.get("title")
    source_path = row.get("source_path") or raw_data.get("source_path")
    if title:
        return str(title)
    if source_path:
        return str(source_path)
    return "__missing_conversation_identifier__"


def _parse_turn_index(turn_index: int | str) -> int:
    try:
        return int(turn_index)
    except (TypeError, ValueError):
        return 0


def _is_missing_value(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")
