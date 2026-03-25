# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Fine-tuning prompts for entity extraction."""

GRAPH_EXTRACTION_PROMPT = """
-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities
- entity_temporal_context: If available, include when this information is valid (e.g., exact date/time, turn order, or relative time such as earlier/later/current). If unavailable, state "time unspecified".
- entity_status: Mark whether the information is current, historical, proposed, corrected, or retracted when this can be inferred from the text.
Format each entity as ("entity"<|><entity_name><|><entity_type><|><entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: an integer score between 1 to 10, indicating strength of the relationship between the source entity and target entity
- relationship_temporal_context: If available, include time markers and update order in the relationship description (e.g., "previously", "later updated", "current").
- relationship_change_type: If applicable, label the relationship as decision, correction, update, plan, unresolved_issue, constraint, or assumption.
Format each relationship as ("relationship"<|><source_entity><|><target_entity><|><relationship_description><|><relationship_strength>)

3. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **##** as the list delimiter.
When temporal context, status, or change type is available, encode it directly in entity_description or relationship_description using compact tags such as [time: ...], [status: ...], [change: ...], [order: ...].
If temporal/status/change information exists in the text, the corresponding tags must be included; omit tags only when the information is unavailable.

4. If you have to translate into {language}, just translate the descriptions, nothing else!

5. When finished, output <|COMPLETE|>.

-Examples-
######################
{examples}

-Real Data-
######################
entity_types: [{entity_types}]
text: {{input_text}}
######################
output:"""

GRAPH_EXTRACTION_JSON_PROMPT = """
-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities
 - entity_temporal_context: If available, include when this information is valid (e.g., exact date/time, turn order, or relative time such as earlier/later/current). If unavailable, state "time unspecified".
 - entity_status: Mark whether the information is current, historical, proposed, corrected, or retracted when this can be inferred from the text.
Format each entity output as a JSON entry with the following format:

{{"name": <entity name>, "type": <type>, "description": <entity description>, "temporal_context": <temporal context>, "status": <status>}}

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: an integer score between 1 to 10, indicating strength of the relationship between the source entity and target entity
- relationship_temporal_context: If available, include time markers and update order.
- relationship_change_type: If applicable, label the relationship as decision, correction, update, plan, unresolved_issue, constraint, or assumption.
Format each relationship as a JSON entry with the following format:

{{"source": <source_entity>, "target": <target_entity>, "relationship": <relationship_description>, "relationship_strength": <relationship_strength>, "temporal_context": <temporal context>, "change_type": <change type>}}

3. Return output in {language} as a single list of all JSON entities and relationships identified in steps 1 and 2.
If temporal/status/change information exists in the text, populate the corresponding JSON fields; leave them empty only when unavailable.

4. If you have to translate into {language}, just translate the descriptions, nothing else!

-Examples-
######################
{examples}

-Real Data-
######################
entity_types: {entity_types}
text: {{input_text}}
######################
output:"""

EXAMPLE_EXTRACTION_TEMPLATE = """
Example {n}:

entity_types: [{entity_types}]
text:
{input_text}
------------------------
output:
{output}
#############################

"""

UNTYPED_EXAMPLE_EXTRACTION_TEMPLATE = """
Example {n}:

text:
{input_text}
------------------------
output:
{output}
#############################

"""


UNTYPED_GRAPH_EXTRACTION_PROMPT = """
-Goal-
Given a text document that is potentially relevant to this activity, first identify all entities needed from the text in order to capture the information and ideas in the text.
Next, report all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: Suggest several labels or categories for the entity. The categories should not be specific, but should be as general as possible.
- entity_description: Comprehensive description of the entity's attributes and activities
- entity_temporal_context: If available, include when this information is valid (e.g., exact date/time, turn order, or relative time such as earlier/later/current). If unavailable, state "time unspecified".
- entity_status: Mark whether the information is current, historical, proposed, corrected, or retracted when this can be inferred from the text.
Format each entity as ("entity"<|><entity_name><|><entity_type><|><entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_temporal_context: If available, include time markers and update order in the relationship description (e.g., "previously", "later updated", "current").
- relationship_change_type: If applicable, label the relationship as decision, correction, update, plan, unresolved_issue, constraint, or assumption.
Format each relationship as ("relationship"<|><source_entity><|><target_entity><|><relationship_description><|><relationship_strength>)

3. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **##** as the list delimiter.
When temporal context, status, or change type is available, encode it directly in entity_description or relationship_description using compact tags such as [time: ...], [status: ...], [change: ...], [order: ...].
If temporal/status/change information exists in the text, the corresponding tags must be included; omit tags only when the information is unavailable.

4. If you have to translate into {language}, just translate the descriptions, nothing else!

5. When finished, output <|COMPLETE|>.

-Examples-
######################
{examples}

-Real Data-
######################
text: {{input_text}}
######################
output:
"""
