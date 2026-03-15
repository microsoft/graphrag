# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing validate_config_names definition."""

import asyncio
import logging
import sys
from typing import TYPE_CHECKING

from graphrag_llm.completion import create_completion
from graphrag_llm.embedding import create_embedding

from graphrag.config.models.graph_rag_config import GraphRagConfig

if TYPE_CHECKING:
    from graphrag_llm.types import LLMEmbeddingResponse

logger = logging.getLogger(__name__)


def validate_config_names(parameters: GraphRagConfig) -> None:
    """Validate config file for model deployment name typos, by running a quick test message for each."""
    for id, config in parameters.completion_models.items():
        llm = create_completion(config)
        try:
            llm.completion(messages="This is an LLM connectivity test. Say Hello World")
            logger.info("LLM Config Params Validated")
        except Exception as e:  # noqa: BLE001
            logger.error(f"LLM configuration error detected.\n{e}")  # noqa
            print(f"Failed to validate language model ({id}) params", e)  # noqa: T201
            sys.exit(1)
    for id, config in parameters.embedding_models.items():
        embed_llm = create_embedding(config)
        try:
            response = asyncio.run(
                embed_llm.embedding_async(
                    input=["This is an LLM Embedding Test String"]
                )
            )
            logger.info("Embedding LLM Config Params Validated")

            if id == parameters.embed_text.embedding_model_id:
                _sync_vector_store_dimensions(parameters, response)

        except Exception as e:  # noqa: BLE001
            logger.error(f"Embedding configuration error detected.\n{e}")  # noqa
            print(f"Failed to validate embedding model ({id}) params", e)  # noqa: T201
            sys.exit(1)


def _sync_vector_store_dimensions(
    parameters: GraphRagConfig,
    response: "LLMEmbeddingResponse",
) -> None:
    """Sync vector store dimensions to match the actual embedding model output."""
    detected = len(response.first_embedding)
    if detected == 0:
        return

    configured = parameters.vector_store.vector_size
    if detected == configured:
        return

    logger.warning(
        "Embedding model produces %d-dimensional vectors but vector_size is "
        "configured as %d. Overriding vector_size to match the model.",
        detected,
        configured,
    )
    parameters.vector_store.vector_size = detected
    for schema in parameters.vector_store.index_schema.values():
        schema.vector_size = detected
