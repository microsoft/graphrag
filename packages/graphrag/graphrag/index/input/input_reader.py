# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineCache' model."""

from __future__ import annotations

import logging
import re
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from graphrag.config.models.input_config import InputConfig
    from graphrag.storage.pipeline_storage import PipelineStorage

logger = logging.getLogger(__name__)


class InputReader(metaclass=ABCMeta):
    """Provide a cache interface for the pipeline."""

    def __init__(self, storage: PipelineStorage, config: InputConfig, **kwargs):
        self._storage = storage
        self._config = config

    async def read_files(self) -> pd.DataFrame:
        """Load files from storage and apply a loader function based on file type. Process metadata on the results if needed."""
        files = list(self._storage.find(re.compile(self._config.file_pattern)))

        if len(files) == 0:
            msg = f"No {self._config.file_type} files found in {self._config.storage.base_dir}"
            raise ValueError(msg)

        files_loaded = []

        for file in files:
            try:
                files_loaded.append(await self.read_file(file))
            except Exception as e:  # noqa: BLE001 (catching Exception is fine here)
                logger.warning("Warning! Error loading file %s. Skipping...", file)
                logger.warning("Error: %s", e)

        logger.info(
            "Found %d %s files, loading %d",
            len(files),
            self._config.file_type,
            len(files_loaded),
        )
        result = pd.concat(files_loaded)
        total_files_log = (
            f"Total number of unfiltered {self._config.file_type} rows: {len(result)}"
        )
        logger.info(total_files_log)
        # Convert metadata columns to strings and collapse them into a JSON object
        if self._config.metadata:
            if all(col in result.columns for col in self._config.metadata):
                # Collapse the metadata columns into a single JSON object column
                result["metadata"] = result[self._config.metadata].apply(
                    lambda row: row.to_dict(), axis=1
                )
            else:
                value_error_msg = (
                    "One or more metadata columns not found in the DataFrame."
                )
                raise ValueError(value_error_msg)

            result[self._config.metadata] = result[self._config.metadata].astype(str)

        return result

    @abstractmethod
    async def read_file(self, path: str) -> pd.DataFrame:
        """Read a file into a DataFrame of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - DataFrame with a row for each document in the file.
        """
