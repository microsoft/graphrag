# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""JSON cleaning and formatting utilities."""


def clean_up_json(json_str: str) -> str:
    """Clean up json string."""
    json_str = (
        json_str.replace("\\n", "")
        .replace("\n", "")
        .replace("\r", "")
        .replace('"[{', "[{")
        .replace('}]"', "}]")
        .replace("\\", "")
        .strip()
    )

    # Remove JSON Markdown Frame
    if json_str.startswith("```json"):
        json_str = json_str[len("```json") :]
    if json_str.endswith("```"):
        json_str = json_str[: len(json_str) - len("```")]

    return json_str
