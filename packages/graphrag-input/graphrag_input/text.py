# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TextFileReader' model."""

import logging
from pathlib import Path

from graphrag_input.hashing import gen_sha512_hash
from graphrag_input.input_reader import InputReader
from graphrag_input.text_document import TextDocument

logger = logging.getLogger(__name__)


class TextFileReader(InputReader):
    """Reader implementation for text files."""

    async def read_file(self, path: str) -> list[TextDocument]:
        """Read a text file into a DataFrame of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - DataFrame with a row for each document in the file.
        """
        text = await self._storage.get(path, encoding=self._encoding)
        document = TextDocument(
            id=gen_sha512_hash({"text": text}, ["text"]),
            title=str(Path(path).name),
            text=text,
            creation_date=await self._storage.get_creation_date(path),
            raw_data=None,
        )
        return [document]
