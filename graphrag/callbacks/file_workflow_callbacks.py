# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A logger that emits updates from the indexing engine to a local file."""

import json
import logging
from io import TextIOWrapper
from pathlib import Path

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks

log = logging.getLogger(__name__)


class FileWorkflowCallbacks(NoopWorkflowCallbacks):
    """A logger that writes to a local file."""

    _out_stream: TextIOWrapper

    def __init__(self, directory: str):
        """Create a new file-based workflow logger."""
        Path(directory).mkdir(parents=True, exist_ok=True)
        self._out_stream = open(  # noqa: PTH123, SIM115
            Path(directory) / "logs.json", "a", encoding="utf-8", errors="strict"
        )

    def error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ):
        """Handle when an error occurs."""
        self._out_stream.write(
            json.dumps(
                {
                    "type": "error",
                    "data": message,
                    "stack": stack,
                    "source": str(cause),
                    "details": details,
                },
                indent=4,
                ensure_ascii=False,
            )
            + "\n"
        )
        message = f"{message} details={details}"
        log.info(message)

    def warning(self, message: str, details: dict | None = None):
        """Handle when a warning occurs."""
        self._out_stream.write(
            json.dumps(
                {"type": "warning", "data": message, "details": details},
                ensure_ascii=False,
            )
            + "\n"
        )
        _print_warning(message)

    def log(self, message: str, details: dict | None = None):
        """Handle when a log message is produced."""
        self._out_stream.write(
            json.dumps(
                {"type": "log", "data": message, "details": details}, ensure_ascii=False
            )
            + "\n"
        )

        message = f"{message} details={details}"
        log.info(message)


def _print_warning(skk):
    log.warning(skk)
