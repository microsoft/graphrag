# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration, loaded from environment variables."""

from pathlib import Path
from typing import Any

from graphrag.config.models.graph_rag_config import GraphRagConfig


def create_graphrag_config(
    values: dict[str, Any] | None = None, root_dir: str | None = None
) -> GraphRagConfig:
    """Load Configuration Parameters from a dictionary."""
    values = values or {}
    if root_dir:
        root_path = Path(root_dir).resolve()
        values["root_dir"] = str(root_path)
    return GraphRagConfig(**values)
