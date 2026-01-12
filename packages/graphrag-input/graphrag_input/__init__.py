# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""GraphRAG input document loading package."""

from graphrag_input.get_property import get_property
from graphrag_input.input_config import InputConfig
from graphrag_input.input_reader import InputReader
from graphrag_input.input_reader_factory import create_input_reader
from graphrag_input.input_type import InputType
from graphrag_input.text_document import TextDocument

__all__ = [
    "InputConfig",
    "InputReader",
    "InputType",
    "TextDocument",
    "create_input_reader",
    "get_property",
]
