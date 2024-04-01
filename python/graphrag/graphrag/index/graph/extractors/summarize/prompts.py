#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A file containing prompts definition."""

SUMMARIZE_PROMPT = """
You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, concise description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we the have full context.

The summary will also include references to real-world knowledge outside the input descriptions, as follows:
"This is an example sentence supported by real-world knowledge [LLM: verify]"
Enrich it as much as you can, this is very important.

#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""
