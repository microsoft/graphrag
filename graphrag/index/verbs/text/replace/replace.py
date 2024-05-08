# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing replace and _apply_replacements methods."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from .typing import Replacement


@verb(name="text_replace")
def text_replace(
    input: VerbInput,
    column: str,
    to: str,
    replacements: list[dict[str, str]],
    **_kwargs: dict,
) -> TableContainer:
    """
    Apply a set of replacements to a piece of text.

    ## Usage
    ```yaml
    verb: text_replace
    args:
        column: <column name> # The name of the column containing the text to replace
        to: <column name> # The name of the column to write the replaced text to
        replacements: # A list of replacements to apply
            - pattern: <string> # The regex pattern to find
            replacement: <string> # The string to replace with
    ```
    """
    output = cast(pd.DataFrame, input.get_input())
    parsed_replacements = [Replacement(**r) for r in replacements]
    output[to] = output[column].apply(
        lambda text: _apply_replacements(text, parsed_replacements)
    )
    return TableContainer(table=output)


def _apply_replacements(text: str, replacements: list[Replacement]) -> str:
    for r in replacements:
        text = text.replace(r.pattern, r.replacement)
    return text
