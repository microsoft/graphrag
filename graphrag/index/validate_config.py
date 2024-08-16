# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing validate_config_names definition."""

import asyncio
import sys

from datashaper import NoopVerbCallbacks

from graphrag.config.models import GraphRagConfig
from graphrag.index.llm import load_llm, load_llm_embeddings
from graphrag.index.progress import (
    ProgressReporter,
)


def validate_config_names(
    reporter: ProgressReporter, parameters: GraphRagConfig
) -> None:
    """Validate config file for LLM deployment name typos."""
    # Validate Chat LLM configs
    llm = load_llm(
        "test-llm",
        parameters.llm.type,
        NoopVerbCallbacks(),
        None,
        parameters.llm.model_dump(),
    )
    try:
        asyncio.run(llm("This is an LLM connectivity test. Say Hello World"))
        reporter.success("LLM Config Params Validated")
    except Exception as e:  # noqa: BLE001
        reporter.error(f"LLM configuration error detected. Exiting...\n{e}")
        sys.exit(1)

    # Validate Embeddings LLM configs
    embed_llm = load_llm_embeddings(
        "test-embed-llm",
        parameters.embeddings.llm.type,
        NoopVerbCallbacks(),
        None,
        parameters.embeddings.llm.model_dump(),
    )
    try:
        asyncio.run(embed_llm(["This is an LLM Embedding Test String"]))
        reporter.success("Embedding LLM Config Params Validated")
    except Exception as e:  # noqa: BLE001
        reporter.error(f"Embedding LLM configuration error detected. Exiting...\n{e}")
        sys.exit(1)
