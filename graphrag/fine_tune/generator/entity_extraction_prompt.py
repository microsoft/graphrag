# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from pathlib import Path
from graphrag.fine_tune.template import (
    GRAPH_EXTRACTION_PROMPT,
    GRAPH_EXTRACTION_JSON_PROMPT,
    EXAMPLE_EXTRACTION_TEMPLATE,
)

from graphrag.index.utils.tokens import num_tokens_from_string

ENTITY_EXTRACTION_FILENAME = "entity_extraction_prompt.txt"


def create_entity_extraction_prompt(
    entity_types: str | list[str],
    docs: list[str],
    examples: list[str],
    model_name: str,
    max_token_count: int,
    json_mode: bool = False,
    output_path: Path | None = None,
) -> str:

    prompt = GRAPH_EXTRACTION_JSON_PROMPT if json_mode else GRAPH_EXTRACTION_PROMPT
    if isinstance(entity_types, list):
        entity_types = ", ".join(entity_types)

    tokens_left = (
        max_token_count
        - num_tokens_from_string(prompt, model=model_name)
        - num_tokens_from_string(entity_types, model=model_name)
    )

    examples_prompt = ""

    # Iterate over examples, while we have tokens left or examples left
    for i, output in enumerate(examples):
        input = docs[i]
        example_formatted = EXAMPLE_EXTRACTION_TEMPLATE.format(
            n=i + 1, input_text=input, entity_types=entity_types, output=output
        )

        print(
            f"Input tokens {num_tokens_from_string(input, model_name)}, output tokens {num_tokens_from_string(output, model_name)}"
        )
        example_tokens = num_tokens_from_string(example_formatted, model=model_name)

        # Squeeze in at least one example
        if i > 0 and example_tokens > tokens_left:
            break

        examples_prompt += example_formatted
        tokens_left -= example_tokens

    prompt = prompt.format(entity_types=entity_types, examples=examples_prompt)

    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

        output_path = output_path / ENTITY_EXTRACTION_FILENAME
        # Write file to output path
        with output_path.open("w") as file:
            file.write(prompt)

    return prompt
