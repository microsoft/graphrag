# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing validate_config_names definition."""

import asyncio
import logging
import sys

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.language_model.manager import ModelManager

logger = logging.getLogger(__name__)


def validate_config_names(parameters: GraphRagConfig) -> None:
    """Validate config file for model deployment name typos, by running a quick test message for each."""
    for id, config in parameters.models.items():
        if config.type in ["chat", "azure_openai", "openai"]:
            llm = ModelManager().register_chat(
                name="test-llm",
                model_type=config.type,
                config=config,
                callbacks=NoopWorkflowCallbacks(),
                cache=None,
            )
            try:
                asyncio.run(
                    llm.achat("This is an LLM connectivity test. Say Hello World")
                )
                logger.info("LLM Config Params Validated")
            except Exception as e:  # noqa: BLE001
                logger.error(f"LLM configuration error detected.\n{e}")  # noqa
                print(f"Failed to validate language model ({id}) params", e)  # noqa: T201
                sys.exit(1)
        elif config.type in ["embedding", "azure_openai_embedding", "openai_embedding"]:
            embed_llm = ModelManager().register_embedding(
                name="test-embed-llm",
                model_type=config.type,
                config=config,
                callbacks=NoopWorkflowCallbacks(),
                cache=None,
            )
            try:
                asyncio.run(
                    embed_llm.aembed_batch(["This is an LLM Embedding Test String"])
                )
                logger.info("Embedding LLM Config Params Validated")
            except Exception as e:  # noqa: BLE001
                logger.error(f"Embedding configuration error detected.\n{e}")  # noqa
                print(f"Failed to validate embedding model ({id}) params", e)  # noqa: T201
                sys.exit(1)
