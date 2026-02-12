# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'InputReader' model."""

from __future__ import annotations

import logging
import re
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from graphrag_storage import Storage

    from graphrag_input.text_document import TextDocument

logger = logging.getLogger(__name__)


class InputReader(metaclass=ABCMeta):
    """Provide a cache interface for the pipeline."""

    def __init__(
        self,
        storage: Storage,
        file_pattern: str,
        encoding: str = "utf-8",
        **kwargs,
    ):
        self._storage = storage
        self._encoding = encoding
        self._file_pattern = file_pattern

    async def read_files(self) -> list[TextDocument]:
        """Load all files from storage and return them as a single list."""
        return [doc async for doc in self]

    def __aiter__(self) -> AsyncIterator[TextDocument]:
        """Return the async iterator, enabling `async for doc in reader`."""
        return self._iterate_files()

    async def _iterate_files(self) -> AsyncIterator[TextDocument]:
        """Async generator that yields documents one at a time as files are loaded."""
        files = list(self._storage.find(re.compile(self._file_pattern)))
        if len(files) == 0:
            msg = f"No {self._file_pattern} matches found in storage"
            logger.warning(msg)
            return

        file_count = len(files)
        doc_count = 0

        for file in files:
            try:
                for doc in await self.read_file(file):
                    doc_count += 1
                    yield doc
            except Exception as e:  # noqa: BLE001 (catching Exception is fine here)
                logger.warning("Warning! Error loading file %s. Skipping...", file)
                logger.warning("Error: %s", e)

        logger.info(
            "Found %d %s files, loading %d",
            file_count,
            self._file_pattern,
            doc_count,
        )
        logger.info(
            "Total number of unfiltered %s rows: %d",
            self._file_pattern,
            doc_count,
        )

    @abstractmethod
    async def read_file(self, path: str) -> list[TextDocument]:
        """Read a file into a list of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - List with an entry for each document in the file.
        """
