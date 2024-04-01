#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine translate strategies package root."""
from .mock import run as run_mock
from .openai import run as run_openai

__all__ = ["run_mock", "run_openai"]
