# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A utility module containing methods for inspecting and verifying dictionary types."""


def dict_has_keys_with_types(
    data: dict, expected_fields: list[tuple[str, type | list[type]]]
) -> bool:
    """Return True if the given dictionary has the given keys with the given types."""
    for field, field_type in expected_fields:
        if field not in data:
            return False

        value = data[field]
        if isinstance(field_type, list):
            if not any(isinstance(value, t) for t in field_type):
                return False
        elif not isinstance(value, field_type):
            return False
    return True
