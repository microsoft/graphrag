import asyncio
import sys
from pathlib import Path

from graphrag.index.progress import (
    ProgressReporter,
)
from graphrag.config.models import GraphRagConfig

from graphrag.config.enums import LLMType
from graphrag.index.llm import load_llm, load_llm_embeddings
from datashaper import NoopVerbCallbacks
from graphrag.llm.types import (
    LLM,
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)

# Function to validate config file for model/deployment name typos
def _validate_config_names(
    reporter: ProgressReporter,
    parameters: GraphRagConfig) -> None:

        # Validate Chat LLM configs
        llm = load_llm(
                "test-llm",
                parameters.llm.type,
                NoopVerbCallbacks(),
                None,
                parameters.llm.model_dump()
            )
        try:
            asyncio.run(llm("This is an LLM connectivity test. Say Hello World"))
            reporter.success("LLM Config Params Validated")
        except Exception as e:
            reporter.error(f"LLM configuration error detected. Exiting...\n{e}")
            sys.exit(1)

        # Validate Embeddings LLM configs
        embed_llm = load_llm_embeddings(
            "test-embed-llm",
            parameters.embeddings.llm.type,
            NoopVerbCallbacks(),
            None,
            parameters.embeddings.llm.model_dump()
        )
        try:
            asyncio.run(embed_llm(["This is an LLM Embedding Test String"]))
            reporter.success("Embedding LLM Config Params Validated")
        except Exception as e:
            reporter.error(f"Embedding LLM configuration error detected. Exiting...\n{e}")
            sys.exit(1)