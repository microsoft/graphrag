# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A utility module datashaper-specific utility methods."""

from typing import cast

from datashaper import TableContainer, VerbInput

_NAMED_INPUTS_REQUIRED = "Named inputs are required"


def get_required_input_table(input: VerbInput, name: str) -> TableContainer:
    """Get a required input table by name."""
    return cast(TableContainer, get_named_input_table(input, name, required=True))


def get_named_input_table(
    input: VerbInput, name: str, required: bool = False
) -> TableContainer | None:
    """Get an input table from datashaper verb-inputs by name."""
    named_inputs = input.named
    if named_inputs is None:
        if not required:
            return None
        raise ValueError(_NAMED_INPUTS_REQUIRED)

    result = named_inputs.get(name)
    if result is None and required:
        msg = f"input '${name}' is required"
        raise ValueError(msg)
    return result
