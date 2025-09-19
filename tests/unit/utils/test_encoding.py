# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.tokenizer.get_tokenizer import get_tokenizer


def test_encode_basic():
    tokenizer = get_tokenizer()
    result = tokenizer.encode("abc def")

    assert result == [13997, 711], "Encoding failed to return expected tokens"


def test_num_tokens_empty_input():
    tokenizer = get_tokenizer()
    result = len(tokenizer.encode(""))

    assert result == 0, "Token count for empty input should be 0"
