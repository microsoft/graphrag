# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine translate strategies package root."""

from .mock import run as run_mock
from .openai import run as run_openai

__all__ = ["run_mock", "run_openai"]
