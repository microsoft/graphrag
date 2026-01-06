# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'JSONFileReader' model."""

import json
import logging

from graphrag.index.input.structured_file_reader import StructuredFileReader
from graphrag.index.input.text_document import TextDocument

logger = logging.getLogger(__name__)


class JSONLinesFileReader(StructuredFileReader):
    """Reader implementation for json files."""

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
        rows = [json.loads(line) for line in text.splitlines()]
        return await self.process_data_columns(rows, path)
