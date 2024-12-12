# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Hashing utilities."""

from collections.abc import Iterable
from hashlib import sha512
from typing import Any


def gen_sha512_hash(item: dict[str, Any], hashcode: Iterable[str]):
    """Generate a SHA512 hash."""
    hashed = "".join([str(item[column]) for column in hashcode])
    return f"{sha512(hashed.encode('utf-8'), usedforsecurity=False).hexdigest()}"
