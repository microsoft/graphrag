# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Module for generating prompts for community report summarization."""

from pathlib import Path

from graphrag.prompt_tune.template.community_report_summarization import (
    COMMUNITY_REPORT_SUMMARIZATION_PROMPT,
)

COMMUNITY_SUMMARIZATION_FILENAME = "community_report_graph.txt"


def create_community_summarization_prompt(
    persona: str,
    role: str,
    report_rating_description: str,
    language: str,
    output_path: Path | None = None,
) -> str:
    """Create a prompt for community summarization. If output_path is provided, write the prompt to a file.

    Parameters
    ----------
    - persona (str): The persona to use for the community summarization prompt
    - role (str): The role to use for the community summarization prompt
    - language (str): The language to use for the community summarization prompt
    - output_path (Path | None): The path to write the prompt to. Default is None. If None, the prompt is not written to a file. Default is None.

    Returns
    -------
    - str: The community summarization prompt
    """
    prompt = COMMUNITY_REPORT_SUMMARIZATION_PROMPT.format(
        persona=persona,
        role=role,
        report_rating_description=report_rating_description,
        language=language,
    )

    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

        output_path = output_path / COMMUNITY_SUMMARIZATION_FILENAME
        # Write file to output path
        with output_path.open("wb") as file:
            file.write(prompt.encode(encoding="utf-8", errors="strict"))

    return prompt
