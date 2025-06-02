# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the pipeline logger factory."""

from __future__ import annotations

import logging
from pathlib import Path

from graphrag.config.enums import ReportingType
from graphrag.config.models.reporting_config import ReportingConfig
from graphrag.logger.blob_workflow_logger import BlobWorkflowLogger
from graphrag.logger.console_workflow_logger import ConsoleWorkflowLogger
from graphrag.logger.file_workflow_logger import FileWorkflowLogger


def create_pipeline_logger(
    config: ReportingConfig | None, root_dir: str | None
) -> None:
    """Create and register a logging handler for the given pipeline config."""
    config = config or ReportingConfig(base_dir="logs", type=ReportingType.file)

    # Get the graphrag logger
    graphrag_logger = logging.getLogger("graphrag")

    # Set the logger level to INFO by default
    graphrag_logger.setLevel(logging.INFO)

    # Prevent propagation to avoid duplicate logs
    graphrag_logger.propagate = False

    # Create the appropriate handler based on configuration
    handler: logging.Handler
    match config.type:
        case ReportingType.file:
            handler = FileWorkflowLogger(
                str(Path(root_dir or "") / (config.base_dir or ""))
            )
        case ReportingType.console:
            handler = ConsoleWorkflowLogger()
        case ReportingType.blob:
            handler = BlobWorkflowLogger(
                config.connection_string,
                config.container_name,
                base_dir=config.base_dir,
                storage_account_blob_url=config.storage_account_blob_url,
            )

    # Register the handler with the graphrag logger
    graphrag_logger.addHandler(handler)
