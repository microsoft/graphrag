# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import sys
import typing
import warnings

from . import _version
from ._search._engine import _base_engine

__all__ = [
    'get_default_logger',
]

_DEFAULT_LOGGING_LEVEL = 'INFO'
_DEFAULT_LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def get_default_logger(
    *,
    level: typing.Optional[str] = _DEFAULT_LOGGING_LEVEL,
    fmt: typing.Optional[str] = _DEFAULT_LOGGING_FORMAT,
    out_file: typing.Optional[str] = None,
    err_file: typing.Optional[str] = None,
    rotation: typing.Optional[str] = None,
    retention: typing.Optional[str] = None,
    serialize: typing.Optional[bool] = None
) -> _base_engine.Logger:
    serialize = serialize if serialize is not None else True
    try:
        import loguru as _loguru

        _loguru_logger = _loguru.logger
        _loguru_logger.remove()  # remove the default logger
        _loguru_logger.add(
            sys.stdout,
            level=level or 'INFO',
            colorize=True,
            backtrace=False,
            diagnose=False,
            catch=False,
            serialize=False
        )
        if out_file:
            _loguru_logger.add(
                out_file,
                level=level or 'INFO',
                rotation=rotation,
                retention=retention,
                colorize=False,
                backtrace=False,
                diagnose=False,
                catch=False,
                serialize=serialize
            )

        _loguru_logger.add(
            sys.stderr,
            level="ERROR",
            colorize=True,
            backtrace=False,
            diagnose=False,
            catch=False,
            serialize=False
        )
        if err_file:
            _loguru_logger.add(
                err_file,
                level='ERROR',
                rotation=rotation,
                retention=retention,
                colorize=False,
                backtrace=False,
                diagnose=False,
                catch=False,
                serialize=serialize
            )

        _loguru_logger = _loguru_logger.bind(namespace=f'{_version.__title__}@{_version.__version__}')
        return typing.cast(_base_engine.Logger, _loguru_logger)

    except ImportError:
        warnings.warn('Required package "loguru" not found. Using default logger instead.')

        import logging as _logging

        _logger = _logging.getLogger(f'{_version.__title__}@{_version.__version__}')
        _logger.setLevel(level or _logging.INFO)
        _logger.propagate = False  # do not propagate to the root logger
        _logger.handlers.clear()

        _stream_handler = _logging.StreamHandler(sys.stdout)
        _stream_handler.setLevel(level or _DEFAULT_LOGGING_LEVEL)
        _stream_handler.setFormatter(_logging.Formatter(fmt or _DEFAULT_LOGGING_FORMAT))
        _logger.addHandler(_stream_handler)

        if out_file:
            _file_handler = _logging.FileHandler(out_file)
            _file_handler.setLevel(level or _DEFAULT_LOGGING_LEVEL)
            _file_handler.setFormatter(_logging.Formatter(fmt or _DEFAULT_LOGGING_FORMAT))
            _logger.addHandler(_file_handler)

        _err_stream_handler = _logging.StreamHandler(sys.stderr)
        _err_stream_handler.setLevel(_logging.ERROR)
        _err_stream_handler.setFormatter(_logging.Formatter(fmt or _DEFAULT_LOGGING_FORMAT))
        _logger.addHandler(_err_stream_handler)

        if err_file:
            _err_file_handler = _logging.FileHandler(err_file)
            _err_file_handler.setLevel(_logging.ERROR)
            _err_file_handler.setFormatter(_logging.Formatter(fmt or _DEFAULT_LOGGING_FORMAT))
            _logger.addHandler(_err_file_handler)

        return typing.cast(_base_engine.Logger, _logger)
