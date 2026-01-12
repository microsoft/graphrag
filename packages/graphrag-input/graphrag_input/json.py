# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'JSONFileReader' model."""

import json
import logging

from graphrag_input.structured_file_reader import StructuredFileReader
from graphrag_input.text_document import TextDocument

logger = logging.getLogger(__name__)


class JSONFileReader(StructuredFileReader):
    """Reader implementation for json files."""

    def __init__(self, file_pattern: str | None = None, **kwargs):
        super().__init__(
            file_pattern=file_pattern if file_pattern is not None else ".*\\.json$",
            **kwargs,
        )

    async def read_file(self, path: str) -> list[TextDocument]:
        """Read a JSON file into a list of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - list with a TextDocument for each row in the file.
        """
        text = await self._storage.get(path, encoding=self._encoding)
        as_json = json.loads(text)
        # json file could just be a single object, or an array of objects
        rows = as_json if isinstance(as_json, list) else [as_json]
        return await self.process_data_columns(rows, path)
