# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""File metrics writer implementation."""

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from graphrag_llm.metrics.metrics_writer import MetricsWriter

if TYPE_CHECKING:
    from graphrag_llm.types import Metrics


class FileMetricsWriter(MetricsWriter):
    """File metrics writer implementation."""

    _log_method: Callable[..., None] | None = None
    _base_dir: Path
    _file_path: Path

    def __init__(self, *, base_dir: str | None = None, **kwargs: Any) -> None:
        """Initialize FileMetricsWriter."""
        self._base_dir = Path(base_dir or Path.cwd()).resolve()
        now = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
        self._file_path = self._base_dir / f"{now}.jsonl"

        self._base_dir.mkdir(parents=True, exist_ok=True)

    def write_metrics(self, *, id: str, metrics: "Metrics") -> None:
        """Write the given metrics."""
        record = json.dumps({"id": id, "metrics": metrics})
        with self._file_path.open("a", encoding="utf-8") as f:
            f.write(f"{record}\n")
