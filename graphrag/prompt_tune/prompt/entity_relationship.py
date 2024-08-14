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
Format each entity as ("entity"{{tuple_delimiter}}<entity_name>{{tuple_delimiter}}<entity_type>{{tuple_delimiter}}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: an integer score between 1 to 10, indicating strength of the relationship between the source entity and target entity
Format each relationship as ("relationship"{{tuple_delimiter}}<source_entity>{{tuple_delimiter}}<target_entity>{{tuple_delimiter}}<relationship_description>{{tuple_delimiter}}<relationship_strength>)

3. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use {{record_delimiter}} as the list delimiter.

4. If you have to translate into {language}, just translate the descriptions, nothing else!

5. When finished, output {{completion_delimiter}}.

######################
-Examples-
######################
Example 1:
Entity_types: ORGANIZATION,PERSON
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
######################
Output:
("entity"{{tuple_delimiter}}CENTRAL INSTITUTION{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}The Central Institution is the Federal Reserve of Verdantis, which is setting interest rates on Monday and Thursday)
{{record_delimiter}}
("entity"{{tuple_delimiter}}MARTIN SMITH{{tuple_delimiter}}PERSON{{tuple_delimiter}}Martin Smith is the chair of the Central Institution)
{{record_delimiter}}
("entity"{{tuple_delimiter}}MARKET STRATEGY COMMITTEE{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}The Central Institution committee makes key decisions about interest rates and the growth of Verdantis's money supply)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}MARTIN SMITH{{tuple_delimiter}}CENTRAL INSTITUTION{{tuple_delimiter}}Martin Smith is the Chair of the Central Institution and will answer questions at a press conference{{tuple_delimiter}}9)
{{completion_delimiter}}

######################
Example 2:
Entity_types: ORGANIZATION
Text:
TechGlobal's (TG) stock skyrocketed in its opening day on the Global Exchange Thursday. But IPO experts warn that the semiconductor corporation's debut on the public markets isn't indicative of how other newly listed companies may perform.

TechGlobal, a formerly public company, was taken private by Vision Holdings in 2014. The well-established chip designer says it powers 85% of premium smartphones.
######################
Output:
("entity"{{tuple_delimiter}}TECHGLOBAL{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}TechGlobal is a stock now listed on the Global Exchange which powers 85% of premium smartphones)
{{record_delimiter}}
("entity"{{tuple_delimiter}}VISION HOLDINGS{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}Vision Holdings is a firm that previously owned TechGlobal)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}TECHGLOBAL{{tuple_delimiter}}VISION HOLDINGS{{tuple_delimiter}}Vision Holdings formerly owned TechGlobal from 2014 until present{{tuple_delimiter}}5)
{{completion_delimiter}}

######################
Example 3:
Entity_types: ORGANIZATION,GEO,PERSON
Text:
Five Aurelians jailed for 8 years in Firuzabad and widely regarded as hostages are on their way home to Aurelia.

The swap orchestrated by Quintara was finalized when $8bn of Firuzi funds were transferred to financial institutions in Krohaara, the capital of Quintara.

The exchange initiated in Firuzabad's capital, Tiruzia, led to the four men and one woman, who are also Firuzi nationals, boarding a chartered flight to Krohaara.

They were welcomed by senior Aurelian officials and are now on their way to Aurelia's capital, Cashion.

The Aurelians include 39-year-old businessman Samuel Namara, who has been held in Tiruzia's Alhamia Prison, as well as journalist Durke Bataglani, 59, and environmentalist Meggie Tazbah, 53, who also holds Bratinas nationality.
######################
Output:
("entity"{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}GEO{{tuple_delimiter}}Firuzabad held Aurelians as hostages)
{{record_delimiter}}
("entity"{{tuple_delimiter}}AURELIA{{tuple_delimiter}}GEO{{tuple_delimiter}}Country seeking to release hostages)
{{record_delimiter}}
("entity"{{tuple_delimiter}}QUINTARA{{tuple_delimiter}}GEO{{tuple_delimiter}}Country that negotiated a swap of money in exchange for hostages)
{{record_delimiter}}
{{record_delimiter}}
("entity"{{tuple_delimiter}}TIRUZIA{{tuple_delimiter}}GEO{{tuple_delimiter}}Capital of Firuzabad where the Aurelians were being held)
{{record_delimiter}}
("entity"{{tuple_delimiter}}KROHAARA{{tuple_delimiter}}GEO{{tuple_delimiter}}Capital city in Quintara)
{{record_delimiter}}
("entity"{{tuple_delimiter}}CASHION{{tuple_delimiter}}GEO{{tuple_delimiter}}Capital city in Aurelia)
{{record_delimiter}}
("entity"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}PERSON{{tuple_delimiter}}Aurelian who spent time in Tiruzia's Alhamia Prison)
{{record_delimiter}}
("entity"{{tuple_delimiter}}ALHAMIA PRISON{{tuple_delimiter}}GEO{{tuple_delimiter}}Prison in Tiruzia)
{{record_delimiter}}
("entity"{{tuple_delimiter}}DURKE BATAGLANI{{tuple_delimiter}}PERSON{{tuple_delimiter}}Aurelian journalist who was held hostage)
{{record_delimiter}}
("entity"{{tuple_delimiter}}MEGGIE TAZBAH{{tuple_delimiter}}PERSON{{tuple_delimiter}}Bratinas national and environmentalist who was held hostage)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}AURELIA{{tuple_delimiter}}Firuzabad negotiated a hostage exchange with Aurelia{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}QUINTARA{{tuple_delimiter}}AURELIA{{tuple_delimiter}}Quintara brokered the hostage exchange between Firuzabad and Aurelia{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}QUINTARA{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}Quintara brokered the hostage exchange between Firuzabad and Aurelia{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}ALHAMIA PRISON{{tuple_delimiter}}Samuel Namara was a prisoner at Alhamia prison{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}MEGGIE TAZBAH{{tuple_delimiter}}Samuel Namara and Meggie Tazbah were exchanged in the same hostage release{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}DURKE BATAGLANI{{tuple_delimiter}}Samuel Namara and Durke Bataglani were exchanged in the same hostage release{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}MEGGIE TAZBAH{{tuple_delimiter}}DURKE BATAGLANI{{tuple_delimiter}}Meggie Tazbah and Durke Bataglani were exchanged in the same hostage release{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}Samuel Namara was a hostage in Firuzabad{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}MEGGIE TAZBAH{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}Meggie Tazbah was a hostage in Firuzabad{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}DURKE BATAGLANI{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}Durke Bataglani was a hostage in Firuzabad{{tuple_delimiter}}2)
{{completion_delimiter}}

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

3. Return output in {language} as a single list of all JSON entities and relationships identified in steps 1 and 2.

4. If you have to translate into {language}, just translate the descriptions, nothing else!

######################
-Examples-
######################
Example 1:
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
######################
Output:
[
  {{"name": "CENTRAL INSTITUTION", "type": "ORGANIZATION", "description": "The Central Institution is the Federal Reserve of Verdantis, which is setting interest rates on Monday and Thursday"}},
  {{"name": "MARTIN SMITH", "type": "PERSON", "description": "Martin Smith is the chair of the Central Institution"}},
  {{"name": "MARKET STRATEGY COMMITTEE", "type": "ORGANIZATION", "description": "The Central Institution committee makes key decisions about interest rates and the growth of Verdantis's money supply"}},
  {{"source": "MARTIN SMITH", "target": "CENTRAL INSTITUTION", "relationship": "Martin Smith is the Chair of the Central Institution and will answer questions at a press conference", "relationship_strength": 9}}
]

######################
Example 2:
Text:
TechGlobal's (TG) stock skyrocketed in its opening day on the Global Exchange Thursday. But IPO experts warn that the semiconductor corporation's debut on the public markets isn't indicative of how other newly listed companies may perform.

TechGlobal, a formerly public company, was taken private by Vision Holdings in 2014. The well-established chip designer says it powers 85% of premium smartphones.
######################
Output:
[
  {{"name": "TECHGLOBAL", "type": "ORGANIZATION", "description": "TechGlobal is a stock now listed on the Global Exchange which powers 85% of premium smartphones"}},
  {{"name": "VISION HOLDINGS", "type": "ORGANIZATION", "description": "Vision Holdings is a firm that previously owned TechGlobal"}},
  {{"source": "TECHGLOBAL", "target": "VISION HOLDINGS", "relationship": "Vision Holdings formerly owned TechGlobal from 2014 until present", "relationship_strength": 5}}
]

######################
Example 3:
Text:
Five Aurelians jailed for 8 years in Firuzabad and widely regarded as hostages are on their way home to Aurelia.

The swap orchestrated by Quintara was finalized when $8bn of Firuzi funds were transferred to financial institutions in Krohaara, the capital of Quintara.

The exchange initiated in Firuzabad's capital, Tiruzia, led to the four men and one woman, who are also Firuzi nationals, boarding a chartered flight to Krohaara.

They were welcomed by senior Aurelian officials and are now on their way to Aurelia's capital, Cashion.

The Aurelians include 39-year-old businessman Samuel Namara, who has been held in Tiruzia's Alhamia Prison, as well as journalist Durke Bataglani, 59, and environmentalist Meggie Tazbah, 53, who also holds Bratinas nationality.
######################
Output:
[
  {{"name": "FIRUZABAD", "type": "GEO", "description": "Firuzabad held Aurelians as hostages"}},
  {{"name": "AURELIA", "type": "GEO", "description": "Country seeking to release hostages"}},
  {{"name": "QUINTARA", "type": "GEO", "description": "Country that negotiated a swap of money in exchange for hostages"}},
  {{"name": "TIRUZIA", "type": "GEO", "description": "Capital of Firuzabad where the Aurelians were being held"}},
  {{"name": "KROHAARA", "type": "GEO", "description": "Capital city in Quintara"}},
  {{"name": "CASHION", "type": "GEO", "description": "Capital city in Aurelia"}},
  {{"name": "SAMUEL NAMARA", "type": "PERSON", "description": "Aurelian who spent time in Tiruzia's Alhamia Prison"}},
  {{"name": "ALHAMIA PRISON", "type": "GEO", "description": "Prison in Tiruzia"}},
  {{"name": "DURKE BATAGLANI", "type": "PERSON", "description": "Aurelian journalist who was held hostage"}},
  {{"name": "MEGGIE TAZBAH", "type": "PERSON", "description": "Bratinas national and environmentalist who was held hostage"}},
  {{"source": "FIRUZABAD", "target": "AURELIA", "relationship": "Firuzabad negotiated a hostage exchange with Aurelia", "relationship_strength": 2}},
  {{"source": "QUINTARA", "target": "AURELIA", "relationship": "Quintara brokered the hostage exchange between Firuzabad and Aurelia", "relationship_strength": 2}},
  {{"source": "QUINTARA", "target": "FIRUZABAD", "relationship": "Quintara brokered the hostage exchange between Firuzabad and Aurelia", "relationship_strength": 2}},
  {{"source": "SAMUEL NAMARA", "target": "ALHAMIA PRISON", "relationship": "Samuel Namara was a prisoner at Alhamia prison", "relationship_strength": 8}},
  {{"source": "SAMUEL NAMARA", "target": "MEGGIE TAZBAH", "relationship": "Samuel Namara and Meggie Tazbah were exchanged in the same hostage release", "relationship_strength": 2}},
  {{"source": "SAMUEL NAMARA", "target": "DURKE BATAGLANI", "relationship": "Samuel Namara and Durke Bataglani were exchanged in the same hostage release", "relationship_strength": 2}},
  {{"source": "MEGGIE TAZBAH", "target": "DURKE BATAGLANI", "relationship": "Meggie Tazbah and Durke Bataglani were exchanged in the same hostage release", "relationship_strength": 2}},
  {{"source": "SAMUEL NAMARA", "target": "FIRUZABAD", "relationship": "Samuel Namara was a hostage in Firuzabad", "relationship_strength": 2}},
  {{"source": "MEGGIE TAZBAH", "target": "FIRUZABAD", "relationship": "Meggie Tazbah was a hostage in Firuzabad", "relationship_strength": 2}},
  {{"source": "DURKE BATAGLANI", "target": "FIRUZABAD", "relationship": "Durke Bataglani was a hostage in Firuzabad", "relationship_strength": 2}}
]



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
Format each entity as ("entity"{{tuple_delimiter}}<entity_name>{{tuple_delimiter}}<entity_type>{{tuple_delimiter}}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
Format each relationship as ("relationship"{{tuple_delimiter}}<source_entity>{{tuple_delimiter}}<target_entity>{{tuple_delimiter}}<relationship_description>{{tuple_delimiter}}<relationship_strength>)

3. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **{{record_delimiter}}** as the list delimiter.

4. If you have to translate into {language}, just translate the descriptions, nothing else!

5. When finished, output {{completion_delimiter}}.

######################
-Examples-
######################
Example 1:
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
######################
Output:
("entity"{{tuple_delimiter}}CENTRAL INSTITUTION{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}The Central Institution is the Federal Reserve of Verdantis, which is setting interest rates on Monday and Thursday)
{{record_delimiter}}
("entity"{{tuple_delimiter}}MARTIN SMITH{{tuple_delimiter}}PERSON{{tuple_delimiter}}Martin Smith is the chair of the Central Institution)
{{record_delimiter}}
("entity"{{tuple_delimiter}}MARKET STRATEGY COMMITTEE{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}The Central Institution committee makes key decisions about interest rates and the growth of Verdantis's money supply)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}MARTIN SMITH{{tuple_delimiter}}CENTRAL INSTITUTION{{tuple_delimiter}}Martin Smith is the Chair of the Central Institution and will answer questions at a press conference{{tuple_delimiter}}9)
{{completion_delimiter}}

######################
Example 2:
Text:
TechGlobal's (TG) stock skyrocketed in its opening day on the Global Exchange Thursday. But IPO experts warn that the semiconductor corporation's debut on the public markets isn't indicative of how other newly listed companies may perform.

TechGlobal, a formerly public company, was taken private by Vision Holdings in 2014. The well-established chip designer says it powers 85% of premium smartphones.
######################
Output:
("entity"{{tuple_delimiter}}TECHGLOBAL{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}TechGlobal is a stock now listed on the Global Exchange which powers 85% of premium smartphones)
{{record_delimiter}}
("entity"{{tuple_delimiter}}VISION HOLDINGS{{tuple_delimiter}}ORGANIZATION{{tuple_delimiter}}Vision Holdings is a firm that previously owned TechGlobal)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}TECHGLOBAL{{tuple_delimiter}}VISION HOLDINGS{{tuple_delimiter}}Vision Holdings formerly owned TechGlobal from 2014 until present{{tuple_delimiter}}5)
{{completion_delimiter}}

######################
Example 3:
Text:
Five Aurelians jailed for 8 years in Firuzabad and widely regarded as hostages are on their way home to Aurelia.

The swap orchestrated by Quintara was finalized when $8bn of Firuzi funds were transferred to financial institutions in Krohaara, the capital of Quintara.

The exchange initiated in Firuzabad's capital, Tiruzia, led to the four men and one woman, who are also Firuzi nationals, boarding a chartered flight to Krohaara.

They were welcomed by senior Aurelian officials and are now on their way to Aurelia's capital, Cashion.

The Aurelians include 39-year-old businessman Samuel Namara, who has been held in Tiruzia's Alhamia Prison, as well as journalist Durke Bataglani, 59, and environmentalist Meggie Tazbah, 53, who also holds Bratinas nationality.
######################
Output:
("entity"{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}GEO{{tuple_delimiter}}Firuzabad held Aurelians as hostages)
{{record_delimiter}}
("entity"{{tuple_delimiter}}AURELIA{{tuple_delimiter}}GEO{{tuple_delimiter}}Country seeking to release hostages)
{{record_delimiter}}
("entity"{{tuple_delimiter}}QUINTARA{{tuple_delimiter}}GEO{{tuple_delimiter}}Country that negotiated a swap of money in exchange for hostages)
{{record_delimiter}}
{{record_delimiter}}
("entity"{{tuple_delimiter}}TIRUZIA{{tuple_delimiter}}GEO{{tuple_delimiter}}Capital of Firuzabad where the Aurelians were being held)
{{record_delimiter}}
("entity"{{tuple_delimiter}}KROHAARA{{tuple_delimiter}}GEO{{tuple_delimiter}}Capital city in Quintara)
{{record_delimiter}}
("entity"{{tuple_delimiter}}CASHION{{tuple_delimiter}}GEO{{tuple_delimiter}}Capital city in Aurelia)
{{record_delimiter}}
("entity"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}PERSON{{tuple_delimiter}}Aurelian who spent time in Tiruzia's Alhamia Prison)
{{record_delimiter}}
("entity"{{tuple_delimiter}}ALHAMIA PRISON{{tuple_delimiter}}GEO{{tuple_delimiter}}Prison in Tiruzia)
{{record_delimiter}}
("entity"{{tuple_delimiter}}DURKE BATAGLANI{{tuple_delimiter}}PERSON{{tuple_delimiter}}Aurelian journalist who was held hostage)
{{record_delimiter}}
("entity"{{tuple_delimiter}}MEGGIE TAZBAH{{tuple_delimiter}}PERSON{{tuple_delimiter}}Bratinas national and environmentalist who was held hostage)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}AURELIA{{tuple_delimiter}}Firuzabad negotiated a hostage exchange with Aurelia{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}QUINTARA{{tuple_delimiter}}AURELIA{{tuple_delimiter}}Quintara brokered the hostage exchange between Firuzabad and Aurelia{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}QUINTARA{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}Quintara brokered the hostage exchange between Firuzabad and Aurelia{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}ALHAMIA PRISON{{tuple_delimiter}}Samuel Namara was a prisoner at Alhamia prison{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}MEGGIE TAZBAH{{tuple_delimiter}}Samuel Namara and Meggie Tazbah were exchanged in the same hostage release{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}DURKE BATAGLANI{{tuple_delimiter}}Samuel Namara and Durke Bataglani were exchanged in the same hostage release{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}MEGGIE TAZBAH{{tuple_delimiter}}DURKE BATAGLANI{{tuple_delimiter}}Meggie Tazbah and Durke Bataglani were exchanged in the same hostage release{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}SAMUEL NAMARA{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}Samuel Namara was a hostage in Firuzabad{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}MEGGIE TAZBAH{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}Meggie Tazbah was a hostage in Firuzabad{{tuple_delimiter}}2)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}DURKE BATAGLANI{{tuple_delimiter}}FIRUZABAD{{tuple_delimiter}}Durke Bataglani was a hostage in Firuzabad{{tuple_delimiter}}2)
{{completion_delimiter}}

######################
-Real Data-
######################
Text: {input_text}
######################
Output:
"""
