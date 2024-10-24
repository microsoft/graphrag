# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing load method definition."""

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from graphrag.index.config.input import PipelineInputConfig
from graphrag.index.storage.pipeline_storage import PipelineStorage
from graphrag.index.utils.hashing import gen_md5_hash
from graphrag.logging.base import ProgressReporter

DEFAULT_FILE_PATTERN = re.compile(
    r".*[\\/](?P<source>[^\\/]+)[\\/](?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})_(?P<author>[^_]+)_\d+\.txt"
)
input_type = "text"
log = logging.getLogger(__name__)


async def load(
    config: PipelineInputConfig,
    progress: ProgressReporter | None,
    storage: PipelineStorage,
) -> pd.DataFrame:
    """Load text inputs from a directory."""

    async def load_file(
        path: str, group: dict | None = None, _encoding: str = "utf-8"
    ) -> dict[str, Any]:
        if group is None:
            group = {}
        text = await storage.get(path, encoding="utf-8")
        new_item = {**group, "text": text}
        new_item["id"] = gen_md5_hash(new_item, new_item.keys())
        new_item["title"] = str(Path(path).name)
        return new_item

    files = list(
        storage.find(
            re.compile(config.file_pattern),
            progress=progress,
            file_filter=config.file_filter,
        )
    )
    if len(files) == 0:
        msg = f"No text files found in {config.base_dir}"
        raise ValueError(msg)
    found_files = f"found text files from {config.base_dir}, found {files}"
    log.info(found_files)

    files_loaded = []

    for file, group in files:
        try:
            files_loaded.append(await load_file(file, group))
        except Exception:  # noqa: BLE001 (catching Exception is fine here)
            log.warning("Warning! Error loading file %s. Skipping...", file)

    log.info("Found %d files, loading %d", len(files), len(files_loaded))

    return pd.DataFrame(files_loaded)
