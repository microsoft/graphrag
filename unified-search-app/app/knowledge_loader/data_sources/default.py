# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Data sources default module."""

import os

container_name = "data"
blob_container_name = os.getenv("BLOB_CONTAINER_NAME", container_name)
blob_account_name = os.getenv("BLOB_ACCOUNT_NAME")

local_data_root = os.getenv("DATA_ROOT")

LISTING_FILE = "listing.json"

if local_data_root is None and blob_account_name is None:
    error_message = (
        "Either DATA_ROOT or BLOB_ACCOUNT_NAME environment variable must be set."
    )
    raise ValueError(error_message)
