"""The EmbeddingsLLM class."""

import dashscope
from typing_extensions import Unpack

from graphrag.llm.base import BaseLLM
from graphrag.llm.types import (
    EmbeddingInput,
    EmbeddingOutput,
    LLMInput,
)


class DashScopeEmbeddingLLM(BaseLLM[EmbeddingInput, EmbeddingOutput]):
    """A text-embedding generator LLM."""
    def __init__(self, llm_config: dict = None):
        log.info(f"llm_config: {llm_config}")
        self.llm_config = llm_config or {}
        self.api_key = self.llm_config.get("api_key", "")
        self.model = self.llm_config.get("model", "text-embedding-v2")

    async def _execute_llm(
            self, input: EmbeddingInput, **kwargs: Unpack[LLMInput]
    ) -> EmbeddingOutput:
        log.info(f"input: {input}")

        response = dashscope.TextEmbedding.call(
            model=self.model,
            input=input,
            api_key=self.api_key
        )

        return [embedding["embedding"] for embedding in response.output["embeddings"]]