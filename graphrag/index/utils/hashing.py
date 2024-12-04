# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Hashing utilities."""

from collections.abc import Iterable
from hashlib import sha256
from typing import Any


def gen_sha256_hash(item: dict[str, Any], hashcode: Iterable[str]):
    """Generate a SHA256 hash."""
    hashed = "".join([str(item[column]) for column in hashcode])
    return f"{sha256(hashed.encode('utf-8'), usedforsecurity=False).hexdigest()}"
