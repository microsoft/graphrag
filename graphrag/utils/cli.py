# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI functions for the GraphRAG module."""

import argparse
from pathlib import Path


def file_exist(path):
    """Check for file existence."""
    if not Path(path).is_file():
        msg = f"File not found: {path}"
        raise argparse.ArgumentTypeError(msg)
    return path


def dir_exist(path):
    """Check for directory existence."""
    if not Path(path).is_dir():
        msg = f"Directory not found: {path}"
        raise argparse.ArgumentTypeError(msg)
    return path
