# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from json_repair import repair_json

"""JSON cleaning and formatting utilities."""


def fix_malformed_json(json_str: str) -> str:
    """Fixup potentially malformed json string using json_repair."""
    return str(repair_json(json_str=json_str, return_objects=False))


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
