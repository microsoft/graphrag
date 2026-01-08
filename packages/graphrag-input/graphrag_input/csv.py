# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CSVFileReader' model."""

import csv
import logging

from graphrag_input.structured_file_reader import StructuredFileReader
from graphrag_input.text_document import TextDocument

logger = logging.getLogger(__name__)


class CSVFileReader(StructuredFileReader):
    """Reader implementation for csv files."""

    async def read_file(self, path: str) -> list[TextDocument]:
        """Read a csv file into a list of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - list with a TextDocument for each row in the file.
        """
        file = await self._storage.get(path)

        reader = csv.DictReader(file.splitlines())
        return await self.process_data_columns(list(reader), path)
