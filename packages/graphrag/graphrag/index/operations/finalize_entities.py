# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Stream-finalize entity rows into an output Table."""

from typing import Any
from uuid import uuid4

from graphrag_storage.tables.table import Table

from graphrag.data_model.schemas import ENTITIES_FINAL_COLUMNS


async def finalize_entities(
    entities_table: Table,
    degree_map: dict[str, int],
) -> list[dict[str, Any]]:
    """Read entity rows, enrich with degree, and write back.

    Streams through the entities table, deduplicates by (title, type),
    assigns degree from the pre-computed degree map, and writes
    each finalized row back to the same table (safe when using
    truncate=True, which reads from the original and writes to
    a temp file).

    Args
    ----
        entities_table: Table
            Opened table for both reading input and writing output.
        degree_map: dict[str, int]
            Pre-computed mapping of entity title to node degree.

    Returns
    -------
        list[dict[str, Any]]
            Sample of up to 5 entity rows for logging.
    """
    sample_rows: list[dict[str, Any]] = []
    seen_entities: set[tuple[str, str]] = set()
    human_readable_id = 0

    async for row in entities_table:
        title = row.get("title")
        entity_type = row.get("type", "")
        if not title or (title, entity_type) in seen_entities:
            continue
        seen_entities.add((title, entity_type))
        row["degree"] = degree_map.get(title, 0)
        row["human_readable_id"] = human_readable_id
        row["id"] = str(uuid4())
        human_readable_id += 1
        out = {col: row.get(col) for col in ENTITIES_FINAL_COLUMNS}
        await entities_table.write(out)
        if len(sample_rows) < 5:
            sample_rows.append(out)

    return sample_rows
