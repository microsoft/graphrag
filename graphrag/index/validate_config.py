# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing validate_config_names definition."""

import asyncio
import sys

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.defaults import language_model_defaults
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.language_model.manager import ModelManager
from graphrag.logger.print_progress import ProgressLogger


def validate_config_names(logger: ProgressLogger, parameters: GraphRagConfig) -> None:
    """Validate config file for LLM deployment name typos."""
    # Validate Chat LLM configs
    # TODO: Replace default_chat_model with a way to select the model
    default_llm_settings = parameters.get_language_model_config("default_chat_model")
    # if max_retries is not set, set it to the default value
    if default_llm_settings.max_retries == -1:
        default_llm_settings.max_retries = language_model_defaults.max_retries
    llm = ModelManager().register_chat(
        name="test-llm",
        model_type=default_llm_settings.type,
        config=default_llm_settings,
        callbacks=NoopWorkflowCallbacks(),
        cache=None,
    )

    try:
        asyncio.run(llm.achat("This is an LLM connectivity test. Say Hello World"))
        logger.success("LLM Config Params Validated")
    except Exception as e:  # noqa: BLE001
        logger.error(f"LLM configuration error detected. Exiting...\n{e}")  # noqa
        sys.exit(1)

    # Validate Embeddings LLM configs
    embedding_llm_settings = parameters.get_language_model_config(
        parameters.embed_text.model_id
    )
    if embedding_llm_settings.max_retries == -1:
        embedding_llm_settings.max_retries = language_model_defaults.max_retries
    embed_llm = ModelManager().register_embedding(
        name="test-embed-llm",
        model_type=embedding_llm_settings.type,
        config=embedding_llm_settings,
        callbacks=NoopWorkflowCallbacks(),
        cache=None,
    )

    try:
        asyncio.run(embed_llm.aembed_batch(["This is an LLM Embedding Test String"]))
        logger.success("Embedding LLM Config Params Validated")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Embedding LLM configuration error detected. Exiting...\n{e}")  # noqa
        sys.exit(1)
