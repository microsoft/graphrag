# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing load method definition."""

import logging
import re
from io import BytesIO
from typing import cast

import pandas as pd

from graphrag.index.config import PipelineCSVInputConfig, PipelineInputConfig
from graphrag.index.progress import ProgressReporter
from graphrag.index.storage import PipelineStorage
from graphrag.index.utils import gen_md5_hash

log = logging.getLogger(__name__)

DEFAULT_FILE_PATTERN = re.compile(r"(?P<filename>[^\\/]).csv$")

input_type = "csv"


async def load(
    config: PipelineInputConfig,
    progress: ProgressReporter | None,
    storage: PipelineStorage,
) -> pd.DataFrame:
    """Load csv inputs from a directory."""
    csv_config = cast(PipelineCSVInputConfig, config)
    log.info("Loading csv files from %s", csv_config.base_dir)

    async def load_file(path: str, group: dict | None) -> pd.DataFrame:
        if group is None:
            group = {}
        buffer = BytesIO(await storage.get(path, as_bytes=True))
        data = pd.read_csv(buffer, encoding=config.encoding or "latin-1")
        additional_keys = group.keys()
        if len(additional_keys) > 0:
            data[[*additional_keys]] = data.apply(
                lambda _row: pd.Series([group[key] for key in additional_keys]), axis=1
            )
        if "id" not in data.columns:
            data["id"] = data.apply(lambda x: gen_md5_hash(x, x.keys()), axis=1)
        if csv_config.source_column is not None and "source" not in data.columns:
            data["source"] = data.apply(lambda x: x[csv_config.source_column], axis=1)
        if csv_config.text_column is not None and "text" not in data.columns:
            data["text"] = data.apply(lambda x: x[csv_config.text_column], axis=1)
        if csv_config.title_column is not None and "title" not in data.columns:
            data["title"] = data.apply(lambda x: x[csv_config.title_column], axis=1)

        if csv_config.timestamp_column is not None:
            fmt = csv_config.timestamp_format
            if fmt is None:
                msg = "Must specify timestamp_format if timestamp_column is specified"
                raise ValueError(msg)
            data["timestamp"] = pd.to_datetime(
                data[csv_config.timestamp_column], format=fmt
            )

            # TODO: Theres probably a less gross way to do this
            if "year" not in data.columns:
                data["year"] = data.apply(lambda x: x["timestamp"].year, axis=1)
            if "month" not in data.columns:
                data["month"] = data.apply(lambda x: x["timestamp"].month, axis=1)
            if "day" not in data.columns:
                data["day"] = data.apply(lambda x: x["timestamp"].day, axis=1)
            if "hour" not in data.columns:
                data["hour"] = data.apply(lambda x: x["timestamp"].hour, axis=1)
            if "minute" not in data.columns:
                data["minute"] = data.apply(lambda x: x["timestamp"].minute, axis=1)
            if "second" not in data.columns:
                data["second"] = data.apply(lambda x: x["timestamp"].second, axis=1)

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
        msg = "No CSV files found in %s" % config.base_dir
        raise ValueError(msg)

    files = [await load_file(file, group) for file, group in files]
    log.info("loading %d csv files", len(files))
    result = pd.concat(files)
    log.info("Total number of unfiltered csv rows: %d", len(result))
    return result
