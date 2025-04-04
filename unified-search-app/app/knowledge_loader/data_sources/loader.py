# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Loader module."""

import json
import logging
import os

from knowledge_loader.data_sources.blob_source import (
    BlobDatasource,
    load_blob_file,
    load_blob_prompt_config,
)
from knowledge_loader.data_sources.default import (
    LISTING_FILE,
    blob_account_name,
    local_data_root,
)
from knowledge_loader.data_sources.local_source import (
    LocalDatasource,
    load_local_prompt_config,
)
from knowledge_loader.data_sources.typing import DatasetConfig, Datasource

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def _get_base_path(
    dataset: str | None, root: str | None, extra_path: str | None = None
) -> str:
    """Construct and return the base path for the given dataset and extra path."""
    return os.path.join(  # noqa: PTH118
        os.path.dirname(os.path.realpath(__file__)),  # noqa: PTH120
        root if root else "",
        dataset if dataset else "",
        *(extra_path.split("/") if extra_path else []),
    )


def create_datasource(dataset_folder: str) -> Datasource:
    """Return a datasource that reads from a local or blob storage parquet file."""
    if blob_account_name is not None and blob_account_name != "":
        return BlobDatasource(dataset_folder)

    base_path = _get_base_path(dataset_folder, local_data_root)
    return LocalDatasource(base_path)


def load_dataset_listing() -> list[DatasetConfig]:
    """Load dataset listing file."""
    datasets = []
    if blob_account_name is not None and blob_account_name != "":
        try:
            blob = load_blob_file(None, LISTING_FILE)
            datasets_str = blob.getvalue().decode("utf-8")
            if datasets_str:
                datasets = json.loads(datasets_str)
        except Exception as e:  # noqa: BLE001
            print(f"Error loading dataset config: {e}")  # noqa T201
            return []
    else:
        base_path = _get_base_path(None, local_data_root, LISTING_FILE)
        with open(base_path, "r") as file:  # noqa: UP015, PTH123
            datasets = json.load(file)

    return [DatasetConfig(**d) for d in datasets]


def load_prompts(dataset: str) -> dict[str, str]:
    """Return the prompts configuration for a specific dataset."""
    if blob_account_name is not None and blob_account_name != "":
        return load_blob_prompt_config(dataset)

    base_path = _get_base_path(dataset, local_data_root, "prompts")
    return load_local_prompt_config(base_path)
