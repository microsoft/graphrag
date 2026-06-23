# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for VectorStore db_uri validation in GraphRagConfig.

Regression tests for:
  https://github.com/microsoft/graphrag/issues/2381

The bug: `store.db_uri.strip` (without parentheses) is a bound method
reference, which is always truthy. The condition `store.db_uri.strip == ""`
was therefore always False, meaning a whitespace-only db_uri was never
replaced with the default, and the subsequent `Path(store.db_uri).resolve()`
would silently succeed with a meaningless path like `Path("   ").resolve()`.

Fix: `store.db_uri.strip()` (with parentheses) calls the method and returns
the stripped string, which is then correctly compared to "".
"""

from pathlib import Path

import pytest

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.models.graph_rag_config import GraphRagConfig

from tests.unit.config.utils import (
    DEFAULT_COMPLETION_MODELS,
    DEFAULT_EMBEDDING_MODELS,
)


def _make_config(db_uri: str | None) -> GraphRagConfig:
    """Construct a minimal GraphRagConfig with the given vector_store db_uri."""
    overrides: dict = {
        "completion_models": DEFAULT_COMPLETION_MODELS,
        "embedding_models": DEFAULT_EMBEDDING_MODELS,
    }
    if db_uri is not None:
        overrides["vector_store"] = {"db_uri": db_uri}
    return GraphRagConfig(**overrides)


class TestVectorStoreDbUriValidation:
    """Tests for _validate_vector_store_db_uri in GraphRagConfig.

    Covers three categories:
      1. Degenerate inputs that should be replaced by the default URI.
      2. Valid non-empty inputs that should be resolved to an absolute path.
      3. The specific regression case: whitespace-only strings must be
         treated as empty and replaced by the default, not forwarded to
         Path.resolve() as-is.
    """

    # ------------------------------------------------------------------
    # Degenerate inputs -- must fall back to the configured default
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "degenerate_uri",
        [
            "",          # empty string
            "   ",       # whitespace only (the regression case from #2381)
            "\t",        # tab-only
            "\n",        # newline-only
            "  \t  \n",  # mixed whitespace
        ],
        ids=[
            "empty_string",
            "spaces_only",
            "tab_only",
            "newline_only",
            "mixed_whitespace",
        ],
    )
    def test_degenerate_db_uri_falls_back_to_default(
        self, degenerate_uri: str
    ) -> None:
        """A blank or whitespace-only db_uri must be replaced with the project default.

        Before the fix, `store.db_uri.strip == ""` compared a bound method
        to a string (always False), so whitespace-only URIs were never
        normalised and were passed directly to Path.resolve(), producing
        a silently wrong absolute path.
        """
        config = _make_config(db_uri=degenerate_uri)
        expected_default = str(
            Path(graphrag_config_defaults.vector_store.db_uri).resolve()
        )
        assert config.vector_store.db_uri == expected_default, (
            f"Expected db_uri to be normalised to the default '{expected_default}' "
            f"when the supplied value is {degenerate_uri!r}, "
            f"but got {config.vector_store.db_uri!r}."
        )

    def test_none_db_uri_falls_back_to_default(self) -> None:
        """Omitting db_uri entirely must also produce the default."""
        config = _make_config(db_uri=None)
        expected_default = str(
            Path(graphrag_config_defaults.vector_store.db_uri).resolve()
        )
        assert config.vector_store.db_uri == expected_default

    # ------------------------------------------------------------------
    # Valid inputs -- must be resolved to an absolute path
    # ------------------------------------------------------------------

    def test_valid_relative_db_uri_is_resolved_to_absolute(self) -> None:
        """A valid relative path must be resolved to an absolute path."""
        config = _make_config(db_uri="output/lancedb")
        result = config.vector_store.db_uri
        assert Path(result).is_absolute(), (
            f"Expected an absolute path but got: {result!r}"
        )
        assert result.endswith("lancedb"), (
            f"Expected path to end with 'lancedb' but got: {result!r}"
        )

    def test_valid_absolute_db_uri_is_preserved(self, tmp_path: Path) -> None:
        """An already-absolute path must pass through Path.resolve unchanged."""
        absolute_uri = str(tmp_path / "lancedb")
        config = _make_config(db_uri=absolute_uri)
        assert config.vector_store.db_uri == str(Path(absolute_uri).resolve())
