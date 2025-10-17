# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing load method definition."""

import logging
from pathlib import Path

import pandas as pd

from graphrag.index.input.input_reader import InputReader
from graphrag.index.utils.hashing import gen_sha512_hash

logger = logging.getLogger(__name__)


class TextFileReader(InputReader):
    """Reader implementation for text files."""

    async def read_file(self, path: str) -> pd.DataFrame:
        """Read a text file into a DataFrame of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - DataFrame with a row for each document in the file.
        """
        text = await self._storage.get(path, encoding=self._config.encoding)
        new_item = {"text": text}
        new_item["id"] = gen_sha512_hash(new_item, new_item.keys())
        new_item["title"] = str(Path(path).name)
        new_item["creation_date"] = await self._storage.get_creation_date(path)
        return pd.DataFrame([new_item])
