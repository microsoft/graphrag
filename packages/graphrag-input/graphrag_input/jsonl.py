# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'JSONLinesFileReader' model."""

import json
import logging

from graphrag_input.structured_file_reader import StructuredFileReader
from graphrag_input.text_document import TextDocument

logger = logging.getLogger(__name__)


class JSONLinesFileReader(StructuredFileReader):
    """Reader implementation for json lines files."""

    def __init__(self, file_pattern: str | None = None, **kwargs):
        super().__init__(
            file_pattern=file_pattern if file_pattern is not None else ".*\\.jsonl$",
            **kwargs,
        )

    async def read_file(self, path: str) -> list[TextDocument]:
        """Read a JSON lines file into a list of documents.

        This differs from standard JSON files in that each line is a separate JSON object.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - list with a TextDocument for each row in the file.
        """
        text = await self._storage.get(path, encoding=self._encoding)
        rows: list[dict] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue

            try:
                parsed_row = json.loads(line)
            except json.JSONDecodeError:
                logger.warning(
                    "Skipping malformed JSONL row in %s at line %s",
                    path,
                    line_number,
                )
                continue

            if isinstance(parsed_row, dict):
                rows.append(parsed_row)
            else:
                logger.warning(
                    "Skipping non-object JSONL row in %s at line %s",
                    path,
                    line_number,
                )

        return await self.process_data_columns(rows, path)
