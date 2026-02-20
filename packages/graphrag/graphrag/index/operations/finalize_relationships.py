# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Stream-finalize relationship rows into an output Table."""

from typing import Any
from uuid import uuid4

from graphrag_storage.tables.table import Table

from graphrag.data_model.schemas import RELATIONSHIPS_FINAL_COLUMNS


async def finalize_relationships(
    relationships_table: Table,
    degree_map: dict[str, int],
) -> list[dict[str, Any]]:
    """Deduplicate relationships, enrich with combined degree, and write.

    Streams through the relationships table, deduplicates by
    (source, target) pair, computes combined_degree as the sum of
    source and target node degrees, and writes each finalized row
    back to the table.

    Args
    ----
        relationships_table: Table
            Opened table for reading and writing relationship rows.
        degree_map: dict[str, int]
            Pre-computed mapping of entity title to node degree.

    Returns
    -------
        list[dict[str, Any]]
            Sample of up to 5 relationship rows for logging.
    """
    sample_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    human_readable_id = 0

    async for row in relationships_table:
        key = (row.get("source", ""), row.get("target", ""))
        if key in seen:
            continue
        seen.add(key)
        row["combined_degree"] = degree_map.get(key[0], 0) + degree_map.get(key[1], 0)
        row["human_readable_id"] = human_readable_id
        row["id"] = str(uuid4())
        human_readable_id += 1
        final = {col: row.get(col) for col in RELATIONSHIPS_FINAL_COLUMNS}
        await relationships_table.write(final)
        if len(sample_rows) < 5:
            sample_rows.append(final)

    return sample_rows
