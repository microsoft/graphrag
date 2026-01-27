# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Fine-tuning prompts for entity summarization."""

ENTITY_SUMMARIZATION_PROMPT = """
{persona}
Using your expertise, you're asked to generate a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, concise description in {language}. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we have the full context.

Enrich it as much as you can with relevant information from the nearby text, this is very important.

If no answer is possible, or the description is empty, only convey information that is provided within the text.
#######
-Data-
Entities: {{entity_name}}
Description List: {{description_list}}
#######
Output:"""
