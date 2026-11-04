# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Provider-managed authentication through the existing LiteLLM factories."""

import asyncio
from unittest.mock import AsyncMock, Mock

import litellm
import pytest
from graphrag_llm.completion import create_completion
from graphrag_llm.config import AuthMethod, MetricsConfig, ModelConfig
from graphrag_llm.embedding import create_embedding
from graphrag_llm.types import LLMCompletionResponse
from litellm.types.utils import Delta, ModelResponseStream, StreamingChoices, Usage
from pydantic import ValidationError


@pytest.mark.parametrize("request_type", ["chat", "embedding"])
@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize("with_metrics", [False, True])
async def test_provider_auth_omits_credentials(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    request_type: str,
    is_async: bool,
    with_metrics: bool,
) -> None:
    monkeypatch.setenv("GRAPHRAG_API_KEY", "unrelated-graphrag-key")
    monkeypatch.setenv("OPENAI_API_KEY", "unrelated-openai-key")
    azure_credential = Mock(side_effect=AssertionError("Azure auth must not run"))
    module = (
        "graphrag_llm.completion.lite_llm_completion"
        if request_type == "chat"
        else "graphrag_llm.embedding.lite_llm_embedding"
    )
    monkeypatch.setattr(f"{module}.DefaultAzureCredential", azure_credential)
    if request_type == "chat":
        model_name = "gpt-4o"
        response = litellm.ModelResponse(
            model=model_name,
            choices=[{"message": {"role": "assistant", "content": "hello"}}],
            usage={"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
        )
        function_name = "acompletion" if is_async else "completion"
    else:
        model_name = "text-embedding-3-small"
        response = litellm.EmbeddingResponse(
            model=model_name,
            data=[{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
            usage=Usage(prompt_tokens=2, completion_tokens=0, total_tokens=2),
        )
        function_name = "aembedding" if is_async else "embedding"
    request = (
        AsyncMock(return_value=response) if is_async else Mock(return_value=response)
    )
    monkeypatch.setattr(litellm, function_name, request)
    config = ModelConfig(
        model_provider="github_copilot",
        model=model_name,
        auth_method=AuthMethod.Provider,
        metrics=MetricsConfig() if with_metrics else None,
        call_args={"timeout": 30, "extra_headers": {"X-Initiator": "agent"}},
    )
    if request_type == "chat":
        model = create_completion(config)
        if is_async:
            result = await model.completion_async(messages="hello")
        else:
            result = model.completion(messages="hello")
        assert isinstance(result, LLMCompletionResponse)
        assert result.content == "hello"
    else:
        model = create_embedding(config)
        if is_async:
            result = await model.embedding_async(input=["hello"])
        else:
            result = model.embedding(input=["hello"])
        assert result.embeddings == [[0.1, 0.2]]
    args = request.call_args.kwargs
    assert args["model"] == f"github_copilot/{model_name}"
    assert args["timeout"] == 30
    assert args["extra_headers"] == {"X-Initiator": "agent"}
    assert "api_key" not in args
    assert "azure_ad_token" not in args
    assert "azure_ad_token_provider" not in args
    azure_credential.assert_not_called()
    if with_metrics:
        metrics = model.metrics_store.get_metrics()
        assert metrics["prompt_tokens"] >= 2
        assert metrics["responses_with_tokens"] >= 1
        assert metrics["successful_response_count"] >= 1
        assert "responses_with_cost" not in metrics
        assert "total_cost" not in metrics
        assert "pricing unavailable" in caplog.text


@pytest.mark.parametrize("request_type", ["chat", "embedding"])
@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize(
    "overrides",
    [
        {"api_key": "unexpected-key"},
        {"azure_ad_token_provider": lambda: "unexpected-token"},
        {"extra_headers": {"AUTHORIZATION": "Bearer unexpected-token"}},
    ],
)
async def test_provider_auth_rejects_per_call_credentials(
    monkeypatch: pytest.MonkeyPatch,
    request_type: str,
    is_async: bool,
    overrides,
) -> None:
    request = Mock(side_effect=AssertionError("LiteLLM must not receive credentials"))
    for function_name in ("completion", "acompletion", "embedding", "aembedding"):
        monkeypatch.setattr(litellm, function_name, request)
    config = ModelConfig(
        model_provider="github_copilot",
        model="gpt-4o" if request_type == "chat" else "text-embedding-3-small",
        auth_method=AuthMethod.Provider,
        metrics=None,
    )
    if request_type == "chat":
        model = create_completion(config)
        if is_async:
            with pytest.raises(ValueError, match="auth_method=provider"):
                await model.completion_async(messages="hello", **overrides)
        else:
            with pytest.raises(ValueError, match="auth_method=provider"):
                model.completion(messages="hello", **overrides)
    else:
        model = create_embedding(config)
        if is_async:
            with pytest.raises(ValueError, match="auth_method=provider"):
                await model.embedding_async(input=["hello"], **overrides)
        else:
            with pytest.raises(ValueError, match="auth_method=provider"):
                model.embedding(input=["hello"], **overrides)
    request.assert_not_called()


@pytest.mark.parametrize("is_async", [False, True])
async def test_provider_auth_streaming(
    monkeypatch: pytest.MonkeyPatch, is_async: bool
) -> None:
    chunk = ModelResponseStream(
        model="gpt-4o",
        choices=[StreamingChoices(delta=Delta(role="assistant", content="hello"))],
    )

    async def chunks():
        await asyncio.sleep(0)
        yield chunk

    request = (
        AsyncMock(return_value=chunks())
        if is_async
        else Mock(return_value=iter([chunk]))
    )
    monkeypatch.setattr(litellm, "acompletion" if is_async else "completion", request)
    model = create_completion(
        ModelConfig(
            model_provider="github_copilot",
            model="gpt-4o",
            auth_method=AuthMethod.Provider,
            metrics=None,
        )
    )
    if is_async:
        response = await model.completion_async(messages="hello", stream=True)
        assert not isinstance(response, LLMCompletionResponse)
        result = [part async for part in response]
    else:
        response = model.completion(messages="hello", stream=True)
        assert not isinstance(response, LLMCompletionResponse)
        result = list(response)
    assert len(result) == 1
    assert request.call_args.kwargs["stream"] is True
    assert "api_key" not in request.call_args.kwargs


@pytest.mark.parametrize("request_type", ["chat", "embedding"])
@pytest.mark.parametrize(
    "auth_method", [AuthMethod.ApiKey, AuthMethod.AzureManagedIdentity]
)
@pytest.mark.parametrize("is_async", [False, True])
async def test_existing_auth_preserves_credential_arguments(
    monkeypatch: pytest.MonkeyPatch,
    request_type: str,
    auth_method: AuthMethod,
    is_async: bool,
) -> None:
    token_provider = Mock()
    module = (
        "graphrag_llm.completion.lite_llm_completion"
        if request_type == "chat"
        else "graphrag_llm.embedding.lite_llm_embedding"
    )
    monkeypatch.setattr(f"{module}.DefaultAzureCredential", Mock())
    get_provider = Mock(return_value=token_provider)
    monkeypatch.setattr(f"{module}.get_bearer_token_provider", get_provider)
    config = ModelConfig(
        model_provider="azure",
        model="gpt-4o",
        azure_deployment_name=f"deployment-{is_async}",
        api_base="https://example.openai.azure.com",
        api_version="2024-06-01",
        auth_method=auth_method,
        api_key="configured-key" if auth_method == AuthMethod.ApiKey else None,
        call_args={"api_key": "override-key"}
        if auth_method == AuthMethod.ApiKey
        else {},
        metrics=None,
    )
    response = (
        litellm.ModelResponse(model="gpt-4o")
        if request_type == "chat"
        else litellm.EmbeddingResponse(model="text-embedding-3-small", data=[])
    )
    request = (
        AsyncMock(return_value=response) if is_async else Mock(return_value=response)
    )
    function_name = (
        ("acompletion" if is_async else "completion")
        if request_type == "chat"
        else ("aembedding" if is_async else "embedding")
    )
    monkeypatch.setattr(litellm, function_name, request)
    if request_type == "chat":
        model = create_completion(config)
        if is_async:
            await model.completion_async(messages="hello")
        else:
            model.completion(messages="hello")
    else:
        model = create_embedding(config)
        if is_async:
            await model.embedding_async(input=["hello"])
        else:
            model.embedding(input=["hello"])
    args = request.call_args.kwargs
    assert args["model"] == f"azure/deployment-{is_async}"
    assert args["api_base"] == config.api_base
    assert args["api_version"] == config.api_version
    if auth_method == AuthMethod.ApiKey:
        assert args["api_key"] == "override-key"
        assert "azure_ad_token_provider" not in args
        get_provider.assert_not_called()
    else:
        assert args["api_key"] is None
        assert args["azure_ad_token_provider"] is token_provider
        get_provider.assert_called_once()


@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize(
    "model_fields",
    [{}, {"model": None}, {"model": "actual-upstream-model"}, {"model": ""}],
)
@pytest.mark.parametrize(
    "requested_model",
    ["github_copilot/text-embedding-3-small", "github_copilot/request-override"],
)
async def test_embedding_response_model_normalization(
    monkeypatch: pytest.MonkeyPatch,
    is_async: bool,
    model_fields,
    requested_model: str,
) -> None:
    response_data = {
        "object": "list",
        "data": [
            {"object": "embedding", "index": 0, "embedding": [0.1, 0.2]},
            {"object": "embedding", "index": 1, "embedding": [0.3, 0.4]},
        ],
        "usage": {"prompt_tokens": 4, "total_tokens": 4},
        **model_fields,
    }
    upstream = Mock(spec=litellm.EmbeddingResponse)
    upstream.model_dump.return_value = response_data.copy()
    request = (
        AsyncMock(return_value=upstream) if is_async else Mock(return_value=upstream)
    )
    monkeypatch.setattr(litellm, "aembedding" if is_async else "embedding", request)
    model = create_embedding(
        ModelConfig(
            model_provider="github_copilot",
            model="text-embedding-3-small",
            auth_method=AuthMethod.Provider,
            metrics=None,
            call_args={"model": requested_model},
        )
    )
    if is_async:
        result = await model.embedding_async(input=["first", "second"])
    else:
        result = model.embedding(input=["first", "second"])
    expected_model = model_fields.get("model")
    if expected_model is None:
        expected_model = requested_model
    assert result.model == expected_model
    assert request.call_args.kwargs["model"] == requested_model
    assert result.embeddings == [[0.1, 0.2], [0.3, 0.4]]
    assert [item.index for item in result.data] == [0, 1]
    assert result.usage.prompt_tokens == 4
    assert result.usage.total_tokens == 4


@pytest.mark.parametrize("is_async", [False, True])
async def test_embedding_response_invalid_model_still_rejected(
    monkeypatch: pytest.MonkeyPatch, is_async: bool
) -> None:
    upstream = Mock(spec=litellm.EmbeddingResponse)
    upstream.model_dump.return_value = {
        "object": "list",
        "data": [],
        "model": 123,
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }
    request = (
        AsyncMock(return_value=upstream) if is_async else Mock(return_value=upstream)
    )
    monkeypatch.setattr(litellm, "aembedding" if is_async else "embedding", request)
    model = create_embedding(
        ModelConfig(
            model_provider="github_copilot",
            model="text-embedding-3-small",
            auth_method=AuthMethod.Provider,
            metrics=None,
        )
    )
    if is_async:
        with pytest.raises(ValidationError, match="model"):
            await model.embedding_async(input=["hello"])
    else:
        with pytest.raises(ValidationError, match="model"):
            model.embedding(input=["hello"])
