# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from datashaper import TableContainer, VerbInput


def str_append(
    input: VerbInput, source_column: str, target_column: str, string_to_append: str
):
    """A custom verb that appends a string to a column"""
    # by convention, we typically use "column" as the input column name and "to" as the output column name, but you can use whatever you want
    # just as long as the "args" in the workflow reference match the function signature
    input_data = input.get_input()
    output_df = input_data.copy()
    output_df[target_column] = output_df[source_column].apply(
        lambda x: f"{x}{string_to_append}"
    )
    return TableContainer(table=output_df)


custom_verbs = {
    "str_append": str_append,
}
