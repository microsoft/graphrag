# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Fine-tuning prompts for entity relationship generation."""

ENTITY_RELATIONSHIPS_GENERATION_PROMPT = """
-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity, include the parenthesis at the beginning and end, as ("entity"{{tuple_delimiter}}<entity_name>{{tuple_delimiter}}<entity_type>{{tuple_delimiter}}<entity_description>)
for example: ("entity"{{tuple_delimiter}}"Microsoft"{{tuple_delimiter}}"organization"{{tuple_delimiter}}"Microsoft is a technology company")

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: an integer score between 1 to 10, indicating strength of the relationship between the source entity and target entity
Format each relationship, include the parenthesis at the beginning and end, as ("relationship"{{tuple_delimiter}}<source_entity>{{tuple_delimiter}}<target_entity>{{tuple_delimiter}}<relationship_description>{{tuple_delimiter}}<relationship_strength>)
for example: ("relationship"{{tuple_delimiter}}"company A"{{tuple_delimiter}}"person A"{{tuple_delimiter}}"company A is currently owned by person A"{{tuple_delimiter}}8)

3. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **{{record_delimiter}}** as the list delimiter.

4. When finished, output {{completion_delimiter}}.

-Real Data-
######################
entity_types: {entity_types}
text: {input_text}
######################
output:
"""

ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT = """
-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities

Format each entity output as a JSON entry with the following format:

{{"name": <entity name>, "type": <type>, "description": <entity description>}}

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: an integer score between 1 to 10, indicating strength of the relationship between the source entity and target entity

Format each relationship as a JSON entry with the following format:

{{"source": <source_entity>, "target": <target_entity>, "relationship": <relationship_description>, "relationship_strength": <relationship_strength>}}

3. Return output in English as a single list of all JSON entities and relationships identified in steps 1 and 2.

-Real Data-
######################
entity_types: {entity_types}
text: {input_text}
######################
output:
"""

UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT = """
-Goal-
Given a text document that is potentially relevant to this activity, first identify all entities needed from the text in order to capture the information and ideas in the text.
Next, report all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: Suggest several labels or categories for the entity. The categories should not be specific, but should be as general as possible.
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{{tuple_delimiter}}<entity_name>{{tuple_delimiter}}<entity_type>{{tuple_delimiter}}<entity_description>

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
 Format each relationship as ("relationship"{{tuple_delimiter}}<source_entity>{{tuple_delimiter}}<target_entity>{{tuple_delimiter}}<relationship_description>{{tuple_delimiter}}<relationship_strength>)

3. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **{{record_delimiter}}** as the list delimiter.

4. When finished, output {{completion_delimiter}}

######################
-Examples-
######################
Text:
The Fed is scheduled to meet on Tuesday and Wednesday, with the central bank planning to release its latest policy decision on Wednesday at 2:00 p.m. ET, followed by a press conference where Fed Chair Jerome Powell will take questions. Investors expect the Federal Open Market Committee to hold its benchmark interest rate steady in a range of 5.25%-5.5%.
######################
Output:
("entity"{{tuple_delimiter}}FED{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}The Fed is the Federal Reserve, which is setting interest rates on Tuesday and Wednesday)
{{record_delimiter}}
("entity"{{tuple_delimiter}}JEROME POWELL{{tuple_delimiter}}PERSON{{tuple_delimiter}}Jerome Powell is the chair of the Federal Reserve)
{{record_delimiter}}
("entity"{{tuple_delimiter}}FEDERAL OPEN MARKET COMMITTEE{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}The Federal Reserve committee makes key decisions about interest rates and the growth of the United States money supply)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}JEROME POWELL{{tuple_delimiter}}FED{{tuple_delimiter}}Jerome Powell is the Chair of the Federal Reserve and will answer questions at a press conference{{tuple_delimiter}}9)
{{completion_delimiter}}
######################
Text:
Arm's (ARM) stock skyrocketed in its opening day on the Nasdaq Thursday. But IPO experts warn that the British chipmaker's debut on the public markets isn't indicative of how other newly listed companies may perform.

Arm, a formerly public company, was taken private by SoftBank in 2016. The well-established chip designer says it powers 99% of premium smartphones.
######################
Output:
("entity"{{tuple_delimiter}}ARM{{tuple_delimiter}}ORGANIZATION, COMPANY{{tuple_delimiter}}Arm is a stock now listed on the Nasdaq which powers 99% of premium smartphones)
{{record_delimiter}}
("entity"{{tuple_delimiter}}SOFTBANK{{tuple_delimiter}}ORGANIZATION, COMPANY{{tuple_delimiter}}SoftBank is a firm that previously owned Arm)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}ARM{{tuple_delimiter}}SOFTBANK{{tuple_delimiter}}SoftBank formerly owned Arm from 2016 until present{{tuple_delimiter}}5)
{{completion_delimiter}}
######################
-Real Data-
######################
Text: {input_text}
######################
Output:
"""
