# Copyright (C) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for the index CLI dry-run path."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from graphrag.cli.index import _run_index
from graphrag.config.enums import IndexingMethod


class TestDryRunLogging:
    """Tests that the dry-run path logs correctly without extra positional args."""

    def _make_config(self):
        """Return a minimal mock config object."""
        config = MagicMock()
        config.cache.type = "memory"
        config.model_dump.return_value = {}
        return config

    @patch("graphrag.cli.index.sys.exit")
    @patch("graphrag.cli.index.validate_config_names")
    @patch("graphrag.cli.index.init_loggers")
    def test_dry_run_exits_zero(self, mock_init_loggers, mock_validate, mock_exit):
        """Dry run must call sys.exit(0) and not raise TypeError."""
        config = self._make_config()

        _run_index(
            config=config,
            method=IndexingMethod.Standard,
            is_update_run=False,
            verbose=False,
            cache=True,
            dry_run=True,
            skip_validation=True,
        )

        mock_exit.assert_called_once_with(0)

    @patch("graphrag.cli.index.sys.exit")
    @patch("graphrag.cli.index.validate_config_names")
    @patch("graphrag.cli.index.init_loggers")
    def test_dry_run_logs_no_extra_args(
        self, mock_init_loggers, mock_validate, mock_exit, caplog
    ):
        """Dry run logger.info call must not pass extra positional args.

        Regression test for Issue #2254 — logger.info("Dry run complete,
        exiting...", True) raised TypeError with certain logging backends.
        The fixed call passes no extra args.
        """
        config = self._make_config()

        with caplog.at_level(logging.INFO, logger="graphrag.cli.index"):
            _run_index(
                config=config,
                method=IndexingMethod.Standard,
                is_update_run=False,
                verbose=False,
                cache=True,
                dry_run=True,
                skip_validation=True,
            )

        # The "Dry run complete" message must appear in the log output.
        assert any("Dry run complete" in r.getMessage() for r in caplog.records)

    @patch("graphrag.cli.index.sys.exit")
    @patch("graphrag.cli.index.validate_config_names")
    @patch("graphrag.cli.index.init_loggers")
    def test_dry_run_does_not_run_pipeline(
        self, mock_init_loggers, mock_validate, mock_exit
    ):
        """When dry_run=True, the async pipeline must not be invoked."""
        config = self._make_config()

        with patch("graphrag.cli.index.asyncio.run") as mock_run:
            _run_index(
                config=config,
                method=IndexingMethod.Standard,
                is_update_run=False,
                verbose=False,
                cache=True,
                dry_run=True,
                skip_validation=True,
            )

            mock_run.assert_not_called()
