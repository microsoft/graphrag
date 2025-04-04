"""
Copyright (c) Microsoft Corporation. All rights reserved.
"""

import logging
import os
from pathlib import Path
from typing import Dict

import pandas as pd
from knowledge_loader.data_sources.typing import Datasource

from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def load_local_prompt_config(base_path="") -> Dict[str, str]:
    # for each file inside folder base_path
    prompts = {}
    for path in os.listdir(base_path):
        with open(os.path.join(base_path, path), "r") as f:
            map_name = path.split(".")[0]
            prompts[map_name] = f.read()
    return prompts


class LocalDatasource(Datasource):
    """
    Datasource that reads from a local parquet file.
    """

    _base_path: str

    def __init__(self, base_path: str):
        self._base_path = base_path

    def read(
        self,
        table: str,
        throw_on_missing: bool = False,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        table = os.path.join(self._base_path, f"{table}.parquet")
        if not os.path.exists(table):
            if throw_on_missing:
                raise FileNotFoundError(f"Table {table} does not exist")
            else:
                print(f"Table {table} does not exist") # noqa T201
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
        cwd = Path(__file__).parent
        root_dir = (cwd / self._base_path).resolve()
        config = load_config(root_dir=root_dir)
        return config
