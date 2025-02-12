# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing load method definition."""

import logging
import re
from io import BytesIO

import pandas as pd

from graphrag.config.models.input_config import InputConfig
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.logger.base import ProgressLogger
from graphrag.storage.pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)

DEFAULT_FILE_PATTERN = re.compile(r"(?P<filename>[^\\/]).csv$")

input_type = "csv"


async def load(
    config: InputConfig,
    progress: ProgressLogger | None,
    storage: PipelineStorage,
) -> pd.DataFrame:
    """Load csv inputs from a directory."""
    log.info("Loading csv files from %s", config.base_dir)

    async def load_file(path: str, group: dict | None) -> pd.DataFrame:
        if group is None:
            group = {}
        buffer = BytesIO(await storage.get(path, as_bytes=True))
        data = pd.read_csv(buffer, encoding=config.encoding)
        additional_keys = group.keys()
        if len(additional_keys) > 0:
            data[[*additional_keys]] = data.apply(
                lambda _row: pd.Series([group[key] for key in additional_keys]), axis=1
            )
        if "id" not in data.columns:
            data["id"] = data.apply(lambda x: gen_sha512_hash(x, x.keys()), axis=1)
        if config.text_column is not None and "text" not in data.columns:
            if config.text_column not in data.columns:
                log.warning(
                    "text_column %s not found in csv file %s",
                    config.text_column,
                    path,
                )
            else:
                data["text"] = data.apply(lambda x: x[config.text_column], axis=1)
        if config.title_column is not None:
            if config.title_column not in data.columns:
                log.warning(
                    "title_column %s not found in csv file %s",
                    config.title_column,
                    path,
                )
            else:
                data["title"] = data.apply(lambda x: x[config.title_column], axis=1)
        else:
            data["title"] = data.apply(lambda _: path, axis=1)

        creation_date = await storage.get_creation_date(path)
        data["creation_date"] = data.apply(lambda _: creation_date, axis=1)

        return data

    file_pattern = (
        re.compile(config.file_pattern)
        if config.file_pattern is not None
        else DEFAULT_FILE_PATTERN
    )
    files = list(
        storage.find(
            file_pattern,
            progress=progress,
            file_filter=config.file_filter,
        )
    )

    if len(files) == 0:
        msg = f"No CSV files found in {config.base_dir}"
        raise ValueError(msg)

    files_loaded = []

    for file, group in files:
        try:
            files_loaded.append(await load_file(file, group))
        except Exception:  # noqa: BLE001 (catching Exception is fine here)
            log.warning("Warning! Error loading csv file %s. Skipping...", file)

    log.info("Found %d csv files, loading %d", len(files), len(files_loaded))
    result = pd.concat(files_loaded)
    total_files_log = f"Total number of unfiltered csv rows: {len(result)}"
    log.info(total_files_log)
    return result
