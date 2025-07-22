# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A utility module containing methods for inspecting and verifying dictionary types."""


def dict_has_keys_with_types(
    data: dict, expected_fields: list[tuple[str, type]], inplace: bool = False
) -> bool:
    """Return True if the given dictionary has the given keys with the given types."""
    for field, field_type in expected_fields:
        if field not in data:
            return False

        value = data[field]
        try:
            cast_value = field_type(value)
            if inplace:
                data[field] = cast_value
        except (TypeError, ValueError):
            return False
    return True
