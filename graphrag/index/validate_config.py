# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing validate_config_names definition."""

import asyncio
import sys

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.llm.load_llm import load_llm, load_llm_embeddings
from graphrag.logger.print_progress import ProgressLogger


def validate_config_names(logger: ProgressLogger, parameters: GraphRagConfig) -> None:
    """Validate config file for LLM deployment name typos."""
    # Validate Chat LLM configs
    llm = load_llm(
        "test-llm",
        parameters.llm,
        callbacks=NoopWorkflowCallbacks(),
        cache=None,
    )
    try:
        asyncio.run(llm("This is an LLM connectivity test. Say Hello World"))
        logger.success("LLM Config Params Validated")
    except Exception as e:  # noqa: BLE001
        logger.error(f"LLM configuration error detected. Exiting...\n{e}")  # noqa
        sys.exit(1)

    # Validate Embeddings LLM configs
    embed_llm = load_llm_embeddings(
        "test-embed-llm",
        parameters.embeddings.llm,
        callbacks=NoopWorkflowCallbacks(),
        cache=None,
    )
    try:
        asyncio.run(embed_llm(["This is an LLM Embedding Test String"]))
        logger.success("Embedding LLM Config Params Validated")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Embedding LLM configuration error detected. Exiting...\n{e}")  # noqa
        sys.exit(1)
