# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import InputFileType, InputType


class InputConfig(BaseModel):
    """The default configuration section for Input."""

    type: InputType = Field(
        description="The input type to use.",
        default=graphrag_config_defaults.input.type,
    )
    file_type: InputFileType = Field(
        description="The input file type to use.",
        default=graphrag_config_defaults.input.file_type,
    )
    base_dir: str = Field(
        description="The input base directory to use.",
        default=graphrag_config_defaults.input.base_dir,
    )
    connection_string: str | None = Field(
        description="The azure blob storage connection string to use.",
        default=graphrag_config_defaults.input.connection_string,
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.",
        default=graphrag_config_defaults.input.storage_account_blob_url,
    )
    container_name: str | None = Field(
        description="The azure blob storage container name to use.",
        default=graphrag_config_defaults.input.container_name,
    )
    encoding: str = Field(
        description="The input file encoding to use.",
        default=defs.graphrag_config_defaults.input.encoding,
    )
    file_pattern: str = Field(
        description="The input file pattern to use.",
        default=graphrag_config_defaults.input.file_pattern,
    )
    file_filter: dict[str, str] | None = Field(
        description="The optional file filter for the input files.",
        default=graphrag_config_defaults.input.file_filter,
    )
    text_column: str = Field(
        description="The input text column to use.",
        default=graphrag_config_defaults.input.text_column,
    )
    title_column: str | None = Field(
        description="The input title column to use.",
        default=graphrag_config_defaults.input.title_column,
    )
    metadata: list[str] | None = Field(
        description="The document attribute columns to use.",
        default=graphrag_config_defaults.input.metadata,
    )
    bucket_name: str | None = Field(
        description="The S3 bucket name to use.",
        default=graphrag_config_defaults.input.bucket_name,
    )
    prefix: str = Field(
        description="The S3 prefix to use.",
        default=graphrag_config_defaults.input.prefix,
    )
    aws_access_key_id: str | None = Field(
        description="The AWS access key ID to use.",
        default=graphrag_config_defaults.input.aws_access_key_id,
    )
    aws_secret_access_key: str | None = Field(
        description="The AWS secret access key to use.",
        default=graphrag_config_defaults.input.aws_secret_access_key,
    )
    region_name: str | None = Field(
        description="The AWS region name to use.",
        default=graphrag_config_defaults.input.region_name,
    )
    endpoint_url: str | None = Field(
        description="The endpoint URL for the S3 API. Useful for S3-compatible storage like MinIO.",
        default=graphrag_config_defaults.input.endpoint_url,
    )
