# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""AWS Bedrock LLM provider definitions."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag.config.models.language_model_config import LanguageModelConfig
    from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
    from graphrag.cache.pipeline_cache import PipelineCache
    from graphrag.language_model.response.base import ModelResponse

import os
import boto3

class BedrockAnthropicChatLLM:
    """AWS Bedrock Anthropic Claude Chat Model provider."""
    def __init__(
        self,
        *,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks | None = None,
        cache: PipelineCache | None = None,
    ) -> None:
        self.config = config
        self.model_id = config.model
        self.endpoint_url = config.api_base or os.environ.get("BEDROCK_ENDPOINT")
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
        )

    async def achat(self, prompt: str, history: list | None = None, **kwargs) -> Any:
        import json
        messages = []
        if history:
            for h in history:
                if isinstance(h, dict) and "role" in h and "content" in h:
                    messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": prompt})
        body = json.dumps({
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
        })
        response = self.client.invoke_model(
            body=body,
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json",
        )
        result = response["body"].read().decode()
        result_json = json.loads(result)
        return result_json.get("content")

class BedrockNovaChatLLM:
    """AWS Bedrock Amazon Nova Chat Model provider."""
    def __init__(
        self,
        *,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks | None = None,
        cache: PipelineCache | None = None,
    ) -> None:
        self.config = config
        self.model_id = config.model
        self.endpoint_url = config.api_base or os.environ.get("BEDROCK_ENDPOINT")
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
        )

    async def achat(self, prompt: str, history: list | None = None, **kwargs) -> Any:
        import json
        body = json.dumps({
            "inputText": prompt,
            "maxGeneratedTokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
            "topP": kwargs.get("top_p", 0.9),
        })
        response = self.client.invoke_model(
            body=body,
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json",
        )
        result = response["body"].read().decode()
        result_json = json.loads(result)
        return result_json.get("results", [{}])[0].get("outputText")

# BedrockChatLLMは汎用モデル用として残す（未対応モデルIDで例外）
class BedrockChatLLM:
    """AWS Bedrock汎用 Chat Model provider (未対応モデルIDで例外)"""
    def __init__(
        self,
        *,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks | None = None,
        cache: PipelineCache | None = None,
    ) -> None:
        self.config = config
        self.model_id = config.model
        self.endpoint_url = config.api_base or os.environ.get("BEDROCK_ENDPOINT")
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
        )

    async def achat(self, prompt: str, history: list | None = None, **kwargs) -> Any:
        raise ValueError(f"BedrockChatLLM: 未対応または不正なモデルIDです: {self.model_id}")

class BedrockEmbeddingLLM:
    """AWS Bedrock Embedding Model provider."""
    def __init__(
        self,
        *,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks | None = None,
        cache: PipelineCache | None = None,
    ) -> None:
        self.config = config
        self.model_id = config.model
        self.endpoint_url = config.api_base or os.environ.get("BEDROCK_ENDPOINT")
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
        )

    async def aembed_batch(self, text_list: list[str], **kwargs) -> list[list[float]]:
        # NOTE: This is a simplified example. Adjust for the actual Bedrock embedding API.
        body = {
            "input": text_list,
            "modelId": self.model_id,
        }
        response = self.client.invoke_model(
            body=body,
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json",
        )
        # 返却値のパースはモデルごとに調整が必要
        return response["body"].read().decode()
