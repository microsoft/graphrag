# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Hashing utilities."""

from collections.abc import Iterable
from hashlib import sha512
from typing import Any


def gen_sha512_hash(item: dict[str, Any], hashcode: Iterable[str]) -> str:
    """Generate a SHA512 hash.

    Parameters
    ----------
    item : dict[str, Any]
        The dictionary containing values to hash.
    hashcode : Iterable[str]
        The keys to include in the hash.

    Returns
    -------
    str
        The SHA512 hash as a hexadecimal string.
    """
    hashed = "".join([str(item[column]) for column in hashcode])
    return f"{sha512(hashed.encode('utf-8'), usedforsecurity=False).hexdigest()}"
