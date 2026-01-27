# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TextFileReader' model."""

import logging
from io import BytesIO
from pathlib import Path

from markitdown import MarkItDown, StreamInfo

from graphrag_input.hashing import gen_sha512_hash
from graphrag_input.input_reader import InputReader
from graphrag_input.text_document import TextDocument

logger = logging.getLogger(__name__)


class MarkItDownFileReader(InputReader):
    """Reader implementation for any file type supported by markitdown.

    https://github.com/microsoft/markitdown
    """

    async def read_file(self, path: str) -> list[TextDocument]:
        """Read a text file into a DataFrame of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - list with a TextDocument for each row in the file.
        """
        bytes = await self._storage.get(path, encoding=self._encoding, as_bytes=True)
        md = MarkItDown()
        result = md.convert_stream(
            BytesIO(bytes), stream_info=StreamInfo(extension=Path(path).suffix)
        )
        text = result.markdown

        document = TextDocument(
            id=gen_sha512_hash({"text": text}, ["text"]),
            title=result.title if result.title else str(Path(path).name),
            text=text,
            creation_date=await self._storage.get_creation_date(path),
            raw_data=None,
        )
        return [document]
