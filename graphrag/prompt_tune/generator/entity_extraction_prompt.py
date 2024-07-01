# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Entity Extraction prompt generator module."""

from pathlib import Path

from graphrag.index.utils.tokens import num_tokens_from_string
from graphrag.prompt_tune.template import (
    EXAMPLE_EXTRACTION_TEMPLATE,
    GRAPH_EXTRACTION_JSON_PROMPT,
    GRAPH_EXTRACTION_PROMPT,
    UNTYPED_EXAMPLE_EXTRACTION_TEMPLATE,
    UNTYPED_GRAPH_EXTRACTION_PROMPT,
)

ENTITY_EXTRACTION_FILENAME = "entity_extraction.txt"


def create_entity_extraction_prompt(
    entity_types: str | list[str] | None,
    docs: list[str],
    examples: list[str],
    model_name: str,
    max_token_count: int,
    json_mode: bool = False,
    output_path: Path | None = None,
) -> str:
    """
    Create a prompt for entity extraction.

    Parameters
    ----------
    - entity_types (str | list[str]): The entity types to extract
    - docs (list[str]): The list of documents to extract entities from
    - examples (list[str]): The list of examples to use for entity extraction
    - model_name (str): The name of the model to use for token counting
    - max_token_count (int): The maximum number of tokens to use for the prompt
    - json_mode (bool): Whether to use JSON mode for the prompt. Default is False
    - output_path (Path | None): The path to write the prompt to. Default is None. If None, the prompt is not written to a file. Default is None.

    Returns
    -------
    - str: The entity extraction prompt
    """
    prompt = (
        (GRAPH_EXTRACTION_JSON_PROMPT if json_mode else GRAPH_EXTRACTION_PROMPT)
        if entity_types
        else UNTYPED_GRAPH_EXTRACTION_PROMPT
    )
    if isinstance(entity_types, list):
        entity_types = ", ".join(entity_types)

    tokens_left = (
        max_token_count
        - num_tokens_from_string(prompt, model=model_name)
        - num_tokens_from_string(entity_types, model=model_name)
        if entity_types
        else 0
    )

    examples_prompt = ""

    # Iterate over examples, while we have tokens left or examples left
    for i, output in enumerate(examples):
        input = docs[i]
        example_formatted = (
            EXAMPLE_EXTRACTION_TEMPLATE.format(
                n=i + 1, input_text=input, entity_types=entity_types, output=output
            )
            if entity_types
            else UNTYPED_EXAMPLE_EXTRACTION_TEMPLATE.format(
                n=i + 1, input_text=input, output=output
            )
        )

        example_tokens = num_tokens_from_string(example_formatted, model=model_name)

        # Squeeze in at least one example
        if i > 0 and example_tokens > tokens_left:
            break

        examples_prompt += example_formatted
        tokens_left -= example_tokens

    prompt = (
        prompt.format(entity_types=entity_types, examples=examples_prompt)
        if entity_types
        else prompt.format(examples=examples_prompt)
    )

    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

        output_path = output_path / ENTITY_EXTRACTION_FILENAME
        # Write file to output path
        with output_path.open("w") as file:
            file.write(prompt)

    return prompt
