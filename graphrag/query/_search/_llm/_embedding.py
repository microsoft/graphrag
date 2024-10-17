# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

import httpx
import openai
import tiktoken
import typing_extensions

from . import _base_llm, _types
from ... import _utils, errors as _errors


class Embedding(_base_llm.BaseEmbedding):
    """
    Synchronous implementation of text embedding generation using the OpenAI
    API.

    This class provides methods for generating embeddings from text using
    OpenAI's embedding models.It handles tokenization, batching, and API
    interaction, and returns combined embeddings for long text inputs.

    Attributes:
        _model: The model identifier for the embedding model.
        _client: The OpenAI client instance used to generate embeddings.
        _max_tokens:
            The maximum number of tokens that can be processed by the model in
            one request.
        _token_encoder:
            The token encoder used to calculate token counts for input text.
    """
    _model: str
    _client: openai.OpenAI
    _max_tokens: int
    _token_encoder: tiktoken.Encoding

    @property
    @typing_extensions.override
    def model(self) -> str:
        return self._model

    @model.setter
    @typing_extensions.override
    def model(self, value: str) -> None:
        self._model = value

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        organization: typing.Optional[str] = None,
        base_url: typing.Optional[str] = None,
        timeout: typing.Optional[float] = None,
        max_retries: typing.Optional[int] = None,
        http_client: typing.Optional[httpx.Client] = None,
        max_tokens: typing.Optional[int] = None,
        token_encoder: typing.Optional[tiktoken.Encoding] = None,
        **kwargs: typing.Any
    ) -> None:
        """
        Initializes the Embedding class with the specified model and OpenAI API
        settings.

        Args:
            model: The model identifier to use for embedding generation.
            api_key: The API key for authenticating with the OpenAI API.
            organization: Optional. The organization ID for the OpenAI API.
            base_url: Optional. The base URL for the OpenAI API.
            timeout: Optional. The request timeout in seconds.
            max_retries:
                Optional. The maximum number of retries for failed requests.
            http_client: Optional. The HTTP client to use for making requests.
            max_tokens:
                Optional. The maximum number of tokens that can be processed in
                one request.
            token_encoder: Optional. The token encoder used for tokenizing text.
            **kwargs: Additional keyword arguments for customization.
        """
        self._client = openai.OpenAI(
            api_key=api_key,
            organization=organization,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries or 3,
            http_client=http_client,
            **_utils.filter_kwargs(openai.OpenAI, kwargs)
        )
        self._model = model
        self._max_tokens = max_tokens or 8191
        self._token_encoder = token_encoder or tiktoken.get_encoding("cl100k_base")

    @typing_extensions.override
    def embed(self, text: str, **kwargs: typing.Any) -> _types.EmbeddingResponse_T:
        """
        Generates an embedding for the given text. If the text is too long, it
        is chunked, and embeddings are generated for each chunk. The results are
        combined into a single embedding.

        Args:
            text: The text to generate an embedding for.
            **kwargs: Additional keyword arguments for customization.

        Returns:
            An EmbeddingResponse containing the generated embeddings.
        """
        chunk_embeddings: typing.List[typing.List[float]] = []
        chunk_lens: typing.List[int] = []
        for chunk in _utils.chunk_text(text, self._max_tokens):
            try:
                embedding = self._client.embeddings.create(
                    input=chunk,
                    model=self._model,
                    **_utils.filter_kwargs(self._client.embeddings.create, kwargs)
                ).data[0].embedding or []
            except openai.APIError as e:
                raise _errors.OpenAIAPIError(e) from e
            chunk_embeddings.append(embedding)
            chunk_lens.append(chunk.__len__() or 0)
        return _utils.combine_embeddings(chunk_embeddings, chunk_lens)

    @typing_extensions.override
    def close(self) -> None:
        self._client.close()


class AsyncEmbedding(_base_llm.BaseAsyncEmbedding):
    """
    Asynchronous implementation of text embedding generation using the OpenAI
    API.

    This class provides methods for asynchronously generating embeddings from
    text using OpenAI's embedding models. It handles tokenization, batching,
    and API interaction, and returns combined embeddings for long text inputs.

    Attributes:
        _model: The model identifier for the embedding model.
        _aclient:
            The asynchronous OpenAI client instance used to generate embeddings.
        _max_tokens:
            The maximum number of tokens that can be processed by the model in
            one request.
        _token_encoder:
            The token encoder used to calculate token counts for input text.
    """
    _model: str
    _aclient: openai.AsyncOpenAI
    _max_tokens: int
    _token_encoder: tiktoken.Encoding

    @property
    @typing_extensions.override
    def model(self) -> str:
        return self._model

    @model.setter
    @typing_extensions.override
    def model(self, value: str) -> None:
        self._model = value

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        organization: typing.Optional[str] = None,
        base_url: typing.Optional[str] = None,
        timeout: typing.Optional[float] = None,
        max_retries: typing.Optional[int] = None,
        http_client: typing.Optional[httpx.AsyncClient] = None,
        max_tokens: typing.Optional[int] = None,
        token_encoder: typing.Optional[tiktoken.Encoding] = None,
        **kwargs: typing.Any
    ) -> None:
        """
        Initializes the AsyncEmbedding class with the specified model and OpenAI
        API settings.

        Args:
            model: The model identifier to use for embedding generation.
            api_key: The API key for authenticating with the OpenAI API.
            organization: Optional. The organization ID for the OpenAI API.
            base_url: Optional. The base URL for the OpenAI API.
            timeout: Optional. The request timeout in seconds.
            max_retries:
                Optional. The maximum number of retries for failed requests.
            http_client:
                Optional. The HTTP client to use for making asynchronous
                requests.
            max_tokens:
                Optional. The maximum number of tokens that can be processed in
                one request.
            token_encoder: Optional. The token encoder used for tokenizing text.
            **kwargs: Additional keyword arguments for customization.
        """
        self._aclient = openai.AsyncOpenAI(
            api_key=api_key,
            organization=organization,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries or 3,
            http_client=http_client,
            **_utils.filter_kwargs(openai.AsyncOpenAI, kwargs)
        )
        self._model = model
        self._max_tokens = max_tokens or 8191
        self._token_encoder = token_encoder or tiktoken.get_encoding("cl100k_base")

    @typing_extensions.override
    async def aembed(self, text: str, **kwargs: typing.Any) -> typing.List[float]:
        """
        Asynchronously generates an embedding for the given text. If the text is
        too long, it is chunked, and embeddings are generated for each chunk.
        The results are combined into a single embedding.

        Args:
            text: The text to generate an embedding for.
            **kwargs: Additional keyword arguments for customization.

        Returns:
            A list of floats representing the combined embeddings.
        """
        chunk_embeddings: typing.List[typing.List[float]] = []
        chunk_lens: typing.List[int] = []
        for chunk in _utils.chunk_text(text, self._max_tokens):
            try:
                embedding = (await self._aclient.embeddings.create(
                    input=chunk,
                    model=self._model,
                    **_utils.filter_kwargs(self._aclient.embeddings.create, kwargs)
                )).data[0].embedding or []
            except openai.APIError as e:
                raise _errors.OpenAIAPIError(e) from e
            chunk_embeddings.append(embedding)
            chunk_lens.append(chunk.__len__() or 0)
        return _utils.combine_embeddings(chunk_embeddings, chunk_lens)

    @typing_extensions.override
    async def aclose(self) -> None:
        await self._aclient.close()
