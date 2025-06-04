# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import OutputType


class OutputConfig(BaseModel):
    """The default configuration section for Output."""

    type: OutputType = Field(
        description="The output type to use.",
        default=graphrag_config_defaults.output.type,
    )
    base_dir: str = Field(
        description="The base directory for the output.",
        default=graphrag_config_defaults.output.base_dir,
    )
    connection_string: str | None = Field(
        description="The storage connection string to use.",
        default=graphrag_config_defaults.output.connection_string,
    )
    container_name: str | None = Field(
        description="The storage container name to use.",
        default=graphrag_config_defaults.output.container_name,
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.",
        default=graphrag_config_defaults.output.storage_account_blob_url,
    )
    cosmosdb_account_url: str | None = Field(
        description="The cosmosdb account url to use.",
        default=graphrag_config_defaults.output.cosmosdb_account_url,
    )
    bucket_name: str | None = Field(
        description="The S3 bucket name to use.",
        default=graphrag_config_defaults.output.bucket_name,
    )
    prefix: str = Field(
        description="The S3 prefix to use.",
        default=graphrag_config_defaults.output.prefix,
    )
    aws_access_key_id: str | None = Field(
        description="The AWS access key ID to use.",
        default=graphrag_config_defaults.output.aws_access_key_id,
    )
    aws_secret_access_key: str | None = Field(
        description="The AWS secret access key to use.",
        default=graphrag_config_defaults.output.aws_secret_access_key,
    )
    region_name: str | None = Field(
        description="The AWS region name to use.",
        default=graphrag_config_defaults.output.region_name,
    )
    endpoint_url: str | None = Field(
        description="The endpoint URL for the S3 API. Useful for S3-compatible storage like MinIO.",
        default=graphrag_config_defaults.output.endpoint_url,
    )
