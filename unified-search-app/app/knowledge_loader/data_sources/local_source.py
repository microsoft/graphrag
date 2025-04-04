# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Local source module."""

import logging
import os
from pathlib import Path

import pandas as pd
from knowledge_loader.data_sources.typing import Datasource

from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def load_local_prompt_config(base_path="") -> dict[str, str]:
    """Load local prompt configuration."""
    # for each file inside folder base_path
    prompts = {}

    for path in os.listdir(base_path):  # noqa: PTH208
        with open(os.path.join(base_path, path), "r") as f:  # noqa: UP015, PTH123, PTH118
            map_name = path.split(".")[0]
            prompts[map_name] = f.read()
    return prompts


class LocalDatasource(Datasource):
    """Datasource that reads from a local parquet file."""

    _base_path: str

    def __init__(self, base_path: str):
        """Init method definition."""
        self._base_path = base_path

    def read(
        self,
        table: str,
        throw_on_missing: bool = False,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """Read file from local source."""
        table = os.path.join(self._base_path, f"{table}.parquet")  # noqa: PTH118

        if not os.path.exists(table):  # noqa: PTH110
            if throw_on_missing:
                error_msg = f"Table {table} does not exist"
                raise FileNotFoundError(error_msg)

            print(f"Table {table} does not exist")  # noqa T201
            return (
                pd.DataFrame(data=[], columns=columns)
                if columns is not None
                else pd.DataFrame()
            )
        return pd.read_parquet(table, columns=columns)

    def read_settings(
        self,
        file: str,
        throw_on_missing: bool = False,
    ) -> GraphRagConfig | None:
        """Read settings file from local source."""
        cwd = Path(__file__).parent
        root_dir = (cwd / self._base_path).resolve()
        return load_config(root_dir=root_dir)
