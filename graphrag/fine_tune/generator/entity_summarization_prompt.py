# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from pathlib import Path
from graphrag.fine_tune.template import ENTITY_SUMMARIZATION_PROMPT

from graphrag.index.utils.tokens import num_tokens_from_string

ENTITY_SUMMARIZATION_FILENAME = "entity_summarization_prompt.txt"


def create_entity_summarization_prompt(
    persona: str,
    output_path: Path | None = None,
) -> str:

    prompt = ENTITY_SUMMARIZATION_PROMPT.format(persona=persona)

    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

        output_path = output_path / ENTITY_SUMMARIZATION_FILENAME
        # Write file to output path
        with output_path.open("w") as file:
            file.write(prompt)

    return prompt
