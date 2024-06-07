# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Entity summarization prompt generation module."""

from pathlib import Path

from graphrag.prompt_tune.template import ENTITY_SUMMARIZATION_PROMPT

ENTITY_SUMMARIZATION_FILENAME = "summarize_descriptions.txt"


def create_entity_summarization_prompt(
    persona: str,
    output_path: Path | None = None,
) -> str:
    """Create a prompt for entity summarization. If output_path is provided, write the prompt to a file.

    Parameters
    ----------
    - persona (str): The persona to use for the entity summarization prompt
    - output_path (Path | None): The path to write the prompt to. Default is None. If None, the prompt is not written to a file. Default is None.
    """
    prompt = ENTITY_SUMMARIZATION_PROMPT.format(persona=persona)

    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

        output_path = output_path / ENTITY_SUMMARIZATION_FILENAME
        # Write file to output path
        with output_path.open("w") as file:
            file.write(prompt)

    return prompt
