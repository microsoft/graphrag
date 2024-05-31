# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from pathlib import Path
from graphrag.fine_tune.template import COMMUNITY_REPORT_SUMMARIZATION_PROMPT


COMMUNITY_SUMMARIZATION_FILENAME = "community_report_summarization_prompt.txt"


def create_community_summarization_prompt(
    persona: str,
    role: str,
    output_path: Path | None = None,
) -> str:

    prompt = COMMUNITY_REPORT_SUMMARIZATION_PROMPT.format(persona=persona, role=role)

    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

        output_path = output_path / COMMUNITY_SUMMARIZATION_FILENAME
        # Write file to output path
        with output_path.open("w") as file:
            file.write(prompt)

    return prompt
