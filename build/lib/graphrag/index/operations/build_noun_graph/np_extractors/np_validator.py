# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Util functions to tag noun phrases for filtering."""


def is_compound(tokens: list[str]) -> bool:
    """List of tokens forms a compound noun phrase."""
    return any(
        "-" in token and len(token.strip()) > 1 and len(token.strip().split("-")) > 1
        for token in tokens
    )


def has_valid_token_length(tokens: list[str], max_length: int) -> bool:
    """Check if all tokens have valid length."""
    return all(len(token) <= max_length for token in tokens)


def is_valid_entity(entity: tuple[str, str], tokens: list[str]) -> bool:
    """Check if the entity is valid."""
    return (entity[1] not in ["CARDINAL", "ORDINAL"] and len(tokens) > 0) or (
        entity[1] in ["CARDINAL", "ORDINAL"]
        and (len(tokens) > 1 or is_compound(tokens))
    )
