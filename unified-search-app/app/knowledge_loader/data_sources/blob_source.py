# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Blob source module."""

import io
import logging
import os
from io import BytesIO

import pandas as pd
import streamlit as st
import yaml
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient
from knowledge_loader.data_sources.typing import Datasource

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.models.graph_rag_config import GraphRagConfig

from .default import blob_account_name, blob_container_name

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@st.cache_data(ttl=60 * 60 * 24)
def _get_container(account_name: str, container_name: str) -> ContainerClient:
    """Return container from blob storage."""
    print("LOGIN---------------")  # noqa T201
    account_url = f"https://{account_name}.blob.core.windows.net"
    default_credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)
    return blob_service_client.get_container_client(container_name)


def load_blob_prompt_config(
    dataset: str,
    account_name: str | None = blob_account_name,
    container_name: str | None = blob_container_name,
) -> dict[str, str]:
    """Load blob prompt configuration."""
    if account_name is None or container_name is None:
        return {}

    container_client = _get_container(account_name, container_name)
    prompts = {}

    prefix = f"{dataset}/prompts"
    for file in container_client.list_blobs(name_starts_with=prefix):
        map_name = file.name.split("/")[-1].split(".")[0]
        prompts[map_name] = (
            container_client.download_blob(file.name).readall().decode("utf-8")
        )

    return prompts


def load_blob_file(
    dataset: str | None,
    file: str | None,
    account_name: str | None = blob_account_name,
    container_name: str | None = blob_container_name,
) -> BytesIO:
    """Load blob file from container."""
    stream = io.BytesIO()

    if account_name is None or container_name is None:
        logger.warning("No account name or container name provided")
        return stream

    container_client = _get_container(account_name, container_name)
    blob_path = f"{dataset}/{file}" if dataset is not None else file

    container_client.download_blob(blob_path).readinto(stream)

    return stream


class BlobDatasource(Datasource):
    """Datasource that reads from a blob storage parquet file."""

    def __init__(self, database: str):
        """Init method definition."""
        self._database = database

    def read(
        self,
        table: str,
        throw_on_missing: bool = False,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """Read file from container."""
        try:
            data = load_blob_file(self._database, f"{table}.parquet")
        except Exception as err:
            if throw_on_missing:
                error_msg = f"Table {table} does not exist"
                raise FileNotFoundError(error_msg) from err
            logger.warning("Table %s does not exist", table)
            return pd.DataFrame(columns=columns) if columns else pd.DataFrame()

        return pd.read_parquet(data, columns=columns)

    def read_settings(
        self,
        file: str,
        throw_on_missing: bool = False,
    ) -> GraphRagConfig | None:
        """Read settings from container."""
        try:
            settings = load_blob_file(self._database, file)
            settings.seek(0)
            str_settings = settings.read().decode("utf-8")
            config = os.path.expandvars(str_settings)
            settings_yaml = yaml.safe_load(config)
            graphrag_config = create_graphrag_config(values=settings_yaml)
        except Exception as err:
            if throw_on_missing:
                error_msg = f"File {file} does not exist"
                raise FileNotFoundError(error_msg) from err

            logger.warning("File %s does not exist", file)
            return None

        return graphrag_config
