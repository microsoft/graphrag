# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.api.prompt_tune import _merge_entity_types, _normalize_entity_types
from graphrag.cli.prompt_tune import _parse_entity_types


def test_parse_entity_types_splits_commas_and_ignores_blanks():
    assert _parse_entity_types("person, organization,, event ") == [
        "person",
        "organization",
        "event",
    ]


def test_parse_entity_types_returns_none_for_empty_input():
    assert _parse_entity_types(None) is None
    assert _parse_entity_types("") is None
    assert _parse_entity_types(" , ") is None


def test_normalize_entity_types_strips_blanks_and_deduplicates():
    assert _normalize_entity_types([" person ", "", "organization", "person"]) == [
        "person",
        "organization",
    ]


def test_merge_entity_types_preserves_user_order_and_deduplicates_generated_values():
    assert _merge_entity_types(
        provided_entity_types=["person", "organization"],
        generated_entity_types=["organization", "event"],
    ) == ["person", "organization", "event"]


def test_merge_entity_types_accepts_string_generated_entity_types():
    assert _merge_entity_types(
        provided_entity_types=["person"],
        generated_entity_types="event",
    ) == ["person", "event"]


def test_merge_entity_types_returns_none_when_no_entity_types_are_available():
    assert (
        _merge_entity_types(
            provided_entity_types=None,
            generated_entity_types=None,
        )
        is None
    )
