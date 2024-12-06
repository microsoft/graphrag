# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing validate_config_names definition."""

import asyncio
import sys

from datashaper import NoopVerbCallbacks

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.llm.load_llm import load_llm, load_llm_embeddings
from graphrag.logging.print_progress import ProgressReporter


def validate_config_names(
    reporter: ProgressReporter, parameters: GraphRagConfig
) -> None:
    """Validate config file for LLM deployment name typos."""
    # Validate Chat LLM configs
    llm = load_llm(
        "test-llm",
        parameters.llm,
        callbacks=NoopVerbCallbacks(),
        cache=None,
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
        parameters.embeddings.llm,
        callbacks=NoopVerbCallbacks(),
        cache=None,
    )
    try:
        asyncio.run(embed_llm(["This is an LLM Embedding Test String"]))
        reporter.success("Embedding LLM Config Params Validated")
    except Exception as e:  # noqa: BLE001
        reporter.error(f"Embedding LLM configuration error detected. Exiting...\n{e}")
        sys.exit(1)
