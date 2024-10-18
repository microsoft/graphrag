# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from ... import errors as _errors

_missing_packages = []

try:
    import PyQt6
except ImportError:
    _missing_packages.append("PyQt6")

try:
    import markdown  # type: ignore
except ImportError:
    _missing_packages.append("markdown")

if _missing_packages:
    raise _errors.MissingPackageError(_missing_packages)

from ._app import main

__all__ = [
    'main',
]
