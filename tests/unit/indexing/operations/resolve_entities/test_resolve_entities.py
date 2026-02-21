# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for the resolve_entities operation."""

from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from graphrag.index.operations.resolve_entities.resolve_entities import (
    resolve_entities,
)


@pytest.fixture
def sample_entities():
    """Create sample entity DataFrame with known duplicates."""
    return pd.DataFrame({
        "title": [
            "Captain Ahab",
            "Moby Dick",
            "Ahab",
            "The Pequod",
            "Ishmael",
            "Pequod",
        ],
        "description": [
            "Captain of the Pequod",
            "The great white whale",
            "The obsessed captain",
            "The whaling ship",
            "The narrator",
            "A whaling vessel",
        ],
    })


@pytest.fixture
def sample_relationships():
    """Create sample relationship DataFrame."""
    return pd.DataFrame({
        "source": ["Ahab", "Captain Ahab", "Ishmael", "Pequod"],
        "target": ["Moby Dick", "The Pequod", "Pequod", "Ahab"],
        "description": [
            "hunts",
            "commands",
            "boards",
            "carries",
        ],
    })


@pytest.fixture
def mock_callbacks():
    """Create mock workflow callbacks."""
    callbacks = MagicMock()
    callbacks.progress = MagicMock()
    return callbacks


def _make_mock_model(response_text: str) -> AsyncMock:
    """Create a mock LLM model that returns the given text."""
    model = AsyncMock()
    model.return_value = response_text
    return model


@pytest.mark.asyncio
async def test_no_duplicates(sample_entities, sample_relationships, mock_callbacks):
    """When LLM finds no duplicates, entities remain unchanged."""
    model = _make_mock_model("NO_DUPLICATES")

    result_entities, result_relationships = await resolve_entities(
        entities=sample_entities.copy(),
        relationships=sample_relationships.copy(),
        callbacks=mock_callbacks,
        model=model,
        prompt="{entity_list}",
        batch_size=200,
        num_threads=1,
    )

    # Titles should be unchanged
    assert list(result_entities["title"]) == list(sample_entities["title"])
    assert list(result_relationships["source"]) == list(
        sample_relationships["source"]
    )


@pytest.mark.asyncio
async def test_simple_duplicates(
    sample_entities, sample_relationships, mock_callbacks
):
    """Ahab → Captain Ahab, Pequod → The Pequod."""
    # LLM response: entity 1 (Captain Ahab) and 3 (Ahab) are the same;
    # entity 4 (The Pequod) and 6 (Pequod) are the same.
    model = _make_mock_model("1, 3\n4, 6")

    result_entities, result_relationships = await resolve_entities(
        entities=sample_entities.copy(),
        relationships=sample_relationships.copy(),
        callbacks=mock_callbacks,
        model=model,
        prompt="{entity_list}",
        batch_size=200,
        num_threads=1,
    )

    # "Ahab" should become "Captain Ahab"
    titles = list(result_entities["title"])
    assert "Ahab" not in titles
    assert titles.count("Captain Ahab") == 2  # both rows unified

    # "Pequod" should become "The Pequod"
    assert "Pequod" not in titles
    assert titles.count("The Pequod") == 2

    # Relationships should also be renamed
    sources = list(result_relationships["source"])
    targets = list(result_relationships["target"])
    assert "Ahab" not in sources
    assert "Ahab" not in targets
    assert "Pequod" not in sources
    assert "Pequod" not in targets


@pytest.mark.asyncio
async def test_llm_failure_graceful(
    sample_entities, sample_relationships, mock_callbacks
):
    """If LLM call fails, entities are returned unchanged."""
    model = AsyncMock(side_effect=Exception("LLM unavailable"))

    result_entities, result_relationships = await resolve_entities(
        entities=sample_entities.copy(),
        relationships=sample_relationships.copy(),
        callbacks=mock_callbacks,
        model=model,
        prompt="{entity_list}",
        batch_size=200,
        num_threads=1,
    )

    # Should fall back to no changes
    assert list(result_entities["title"]) == list(sample_entities["title"])


@pytest.mark.asyncio
async def test_single_entity_skips():
    """With fewer than 2 entities, resolution is skipped entirely."""
    entities = pd.DataFrame({"title": ["Only One"]})
    relationships = pd.DataFrame({"source": [], "target": []})
    callbacks = MagicMock()
    callbacks.progress = MagicMock()
    model = _make_mock_model("should not be called")

    result_entities, _ = await resolve_entities(
        entities=entities,
        relationships=relationships,
        callbacks=callbacks,
        model=model,
        prompt="{entity_list}",
        batch_size=200,
        num_threads=1,
    )

    # Model should not have been called
    model.assert_not_called()
    assert list(result_entities["title"]) == ["Only One"]


@pytest.mark.asyncio
async def test_batch_splitting(mock_callbacks):
    """Entities are split into batches of the configured size."""
    # 5 entities, batch_size=2 → 3 batches
    entities = pd.DataFrame({
        "title": ["A", "B", "C", "D", "E"],
        "description": [""] * 5,
    })
    relationships = pd.DataFrame({"source": ["A"], "target": ["B"]})

    model = _make_mock_model("NO_DUPLICATES")

    await resolve_entities(
        entities=entities.copy(),
        relationships=relationships.copy(),
        callbacks=mock_callbacks,
        model=model,
        prompt="{entity_list}",
        batch_size=2,
        num_threads=1,
    )

    # Model should have been called 3 times (ceil(5/2))
    assert model.call_count == 3


@pytest.mark.asyncio
async def test_missing_title_column(mock_callbacks):
    """If there's no title column, skip resolution."""
    entities = pd.DataFrame({"name": ["A", "B"]})
    relationships = pd.DataFrame({"source": ["A"], "target": ["B"]})
    model = _make_mock_model("should not be called")

    result_entities, _ = await resolve_entities(
        entities=entities,
        relationships=relationships,
        callbacks=mock_callbacks,
        model=model,
        prompt="{entity_list}",
        batch_size=200,
        num_threads=1,
    )

    model.assert_not_called()
    assert list(result_entities.columns) == ["name"]
