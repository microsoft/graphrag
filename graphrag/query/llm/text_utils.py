# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Text Utilities for LLM."""

import json
import logging
import re
from collections.abc import Iterator
from itertools import islice

from json_repair import repair_json

import graphrag.config.defaults as defs
from graphrag.tokenizer.get_tokenizer import get_tokenizer
from graphrag.tokenizer.tokenizer import Tokenizer

logger = logging.getLogger(__name__)


def batched(iterable: Iterator, n: int):
    """
    Batch data into tuples of length n. The last batch may be shorter.

    Taken from Python's cookbook: https://docs.python.org/3/library/itertools.html#itertools.batched
    """
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        value_error = "n must be at least one"
        raise ValueError(value_error)
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def chunk_text(text: str, max_tokens: int, tokenizer: Tokenizer | None = None):
    """Chunk text by token length."""
    if tokenizer is None:
        tokenizer = get_tokenizer(encoding_model=defs.ENCODING_MODEL)
    tokens = tokenizer.encode(text)  # type: ignore
    chunk_iterator = batched(iter(tokens), max_tokens)
    yield from (tokenizer.decode(list(chunk)) for chunk in chunk_iterator)


def try_parse_json_object(input: str, verbose: bool = True) -> tuple[str, dict]:
    """JSON cleaning and formatting utilities."""
    # Sometimes, the LLM returns a json string with some extra description, this function will clean it up.

    result = None
    try:
        # Try parse first
        result = json.loads(input)
    except json.JSONDecodeError:
        if verbose:
            logger.warning("Error decoding faulty json, attempting repair")

    if result:
        return input, result

    pattern = r"\{(.*)\}"
    match = re.search(pattern, input, re.DOTALL)
    input = "{" + match.group(1) + "}" if match else input

    # Clean up json string.
    input = (
        input.replace("{{", "{")
        .replace("}}", "}")
        .replace('"[{', "[{")
        .replace('}]"', "}]")
        .replace("\\", " ")
        .replace("\\n", " ")
        .replace("\n", " ")
        .replace("\r", "")
        .strip()
    )

    # Remove JSON Markdown Frame
    if input.startswith("```json"):
        input = input[len("```json") :]
    if input.endswith("```"):
        input = input[: len(input) - len("```")]

    try:
        result = json.loads(input)
    except json.JSONDecodeError:
        # Fixup potentially malformed json string using json_repair.
        input = str(repair_json(json_str=input, return_objects=False))

        # Generate JSON-string output using best-attempt prompting & parsing techniques.
        try:
            result = json.loads(input)
        except json.JSONDecodeError:
            if verbose:
                logger.exception("error loading json, json=%s", input)
            return input, {}
        else:
            if not isinstance(result, dict):
                if verbose:
                    logger.exception("not expected dict type. type=%s:", type(result))
                return input, {}
            return input, result
    else:
        return input, result
