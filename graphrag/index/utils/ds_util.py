# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A utility module datashaper-specific utility methods."""

from datashaper import TableContainer, VerbInput

_NAMED_INPUTS_REQUIRED = "Named inputs are required"


def get_required_input_table(input: VerbInput, name: str) -> TableContainer:
    """Get the required input table."""
    named_inputs = input.named
    if named_inputs is None:
        raise ValueError(_NAMED_INPUTS_REQUIRED)
    result = named_inputs.get(name)
    if result is None:
        msg = f"input '${name}' is required"
        raise ValueError(msg)
    return result
