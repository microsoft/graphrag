# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'InputReaderFactory' model."""

import logging

from graphrag_common.factory import Factory

from graphrag.config.enums import InputFileType
from graphrag.index.input.csv import CSVFileReader
from graphrag.index.input.input_reader import InputReader
from graphrag.index.input.json import JSONFileReader
from graphrag.index.input.text import TextFileReader

logger = logging.getLogger(__name__)


class InputReaderFactory(Factory[InputReader]):
    """Factory for creating Input Reader instances."""


input_reader_factory = InputReaderFactory()
input_reader_factory.register(InputFileType.text, TextFileReader)
input_reader_factory.register(InputFileType.csv, CSVFileReader)
input_reader_factory.register(InputFileType.json, JSONFileReader)
