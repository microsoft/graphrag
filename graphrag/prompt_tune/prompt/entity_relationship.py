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
Format each entity as ("entity"<|><entity_name><|><entity_type><|><entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: an integer score between 1 to 10, indicating strength of the relationship between the source entity and target entity
Format each relationship as ("relationship"<|><source_entity><|><target_entity><|><relationship_description><|><relationship_strength>)

3. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use ## as the list delimiter.

4. If you have to translate into {language}, just translate the descriptions, nothing else!

5. When finished, output <|COMPLETE|>.

######################
-Examples-
######################
Example 1:
Entity_types: ORGANIZATION,PERSON
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
######################
Output:
("entity"<|>CENTRAL INSTITUTION<|>ORGANIZATION<|>The Central Institution is the Federal Reserve of Verdantis, which is setting interest rates on Monday and Thursday)
##
("entity"<|>MARTIN SMITH<|>PERSON<|>Martin Smith is the chair of the Central Institution)
##
("entity"<|>MARKET STRATEGY COMMITTEE<|>ORGANIZATION<|>The Central Institution committee makes key decisions about interest rates and the growth of Verdantis's money supply)
##
("relationship"<|>MARTIN SMITH<|>CENTRAL INSTITUTION<|>Martin Smith is the Chair of the Central Institution and will answer questions at a press conference<|>9)
<|COMPLETE|>

######################
Example 2:
Entity_types: ORGANIZATION
Text:
TechGlobal's (TG) stock skyrocketed in its opening day on the Global Exchange Thursday. But IPO experts warn that the semiconductor corporation's debut on the public markets isn't indicative of how other newly listed companies may perform.

TechGlobal, a formerly public company, was taken private by Vision Holdings in 2014. The well-established chip designer says it powers 85% of premium smartphones.
######################
Output:
("entity"<|>TECHGLOBAL<|>ORGANIZATION<|>TechGlobal is a stock now listed on the Global Exchange which powers 85% of premium smartphones)
##
("entity"<|>VISION HOLDINGS<|>ORGANIZATION<|>Vision Holdings is a firm that previously owned TechGlobal)
##
("relationship"<|>TECHGLOBAL<|>VISION HOLDINGS<|>Vision Holdings formerly owned TechGlobal from 2014 until present<|>5)
<|COMPLETE|>

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
("entity"<|>FIRUZABAD<|>GEO<|>Firuzabad held Aurelians as hostages)
##
("entity"<|>AURELIA<|>GEO<|>Country seeking to release hostages)
##
("entity"<|>QUINTARA<|>GEO<|>Country that negotiated a swap of money in exchange for hostages)
##
##
("entity"<|>TIRUZIA<|>GEO<|>Capital of Firuzabad where the Aurelians were being held)
##
("entity"<|>KROHAARA<|>GEO<|>Capital city in Quintara)
##
("entity"<|>CASHION<|>GEO<|>Capital city in Aurelia)
##
("entity"<|>SAMUEL NAMARA<|>PERSON<|>Aurelian who spent time in Tiruzia's Alhamia Prison)
##
("entity"<|>ALHAMIA PRISON<|>GEO<|>Prison in Tiruzia)
##
("entity"<|>DURKE BATAGLANI<|>PERSON<|>Aurelian journalist who was held hostage)
##
("entity"<|>MEGGIE TAZBAH<|>PERSON<|>Bratinas national and environmentalist who was held hostage)
##
("relationship"<|>FIRUZABAD<|>AURELIA<|>Firuzabad negotiated a hostage exchange with Aurelia<|>2)
##
("relationship"<|>QUINTARA<|>AURELIA<|>Quintara brokered the hostage exchange between Firuzabad and Aurelia<|>2)
##
("relationship"<|>QUINTARA<|>FIRUZABAD<|>Quintara brokered the hostage exchange between Firuzabad and Aurelia<|>2)
##
("relationship"<|>SAMUEL NAMARA<|>ALHAMIA PRISON<|>Samuel Namara was a prisoner at Alhamia prison<|>8)
##
("relationship"<|>SAMUEL NAMARA<|>MEGGIE TAZBAH<|>Samuel Namara and Meggie Tazbah were exchanged in the same hostage release<|>2)
##
("relationship"<|>SAMUEL NAMARA<|>DURKE BATAGLANI<|>Samuel Namara and Durke Bataglani were exchanged in the same hostage release<|>2)
##
("relationship"<|>MEGGIE TAZBAH<|>DURKE BATAGLANI<|>Meggie Tazbah and Durke Bataglani were exchanged in the same hostage release<|>2)
##
("relationship"<|>SAMUEL NAMARA<|>FIRUZABAD<|>Samuel Namara was a hostage in Firuzabad<|>2)
##
("relationship"<|>MEGGIE TAZBAH<|>FIRUZABAD<|>Meggie Tazbah was a hostage in Firuzabad<|>2)
##
("relationship"<|>DURKE BATAGLANI<|>FIRUZABAD<|>Durke Bataglani was a hostage in Firuzabad<|>2)
<|COMPLETE|>

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
Format each entity as ("entity"<|><entity_name><|><entity_type><|><entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
Format each relationship as ("relationship"<|><source_entity><|><target_entity><|><relationship_description><|><relationship_strength>)

3. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **##** as the list delimiter.

4. If you have to translate into {language}, just translate the descriptions, nothing else!

5. When finished, output <|COMPLETE|>.

######################
-Examples-
######################
Example 1:
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
######################
Output:
("entity"<|>CENTRAL INSTITUTION<|>ORGANIZATION<|>The Central Institution is the Federal Reserve of Verdantis, which is setting interest rates on Monday and Thursday)
##
("entity"<|>MARTIN SMITH<|>PERSON<|>Martin Smith is the chair of the Central Institution)
##
("entity"<|>MARKET STRATEGY COMMITTEE<|>ORGANIZATION<|>The Central Institution committee makes key decisions about interest rates and the growth of Verdantis's money supply)
##
("relationship"<|>MARTIN SMITH<|>CENTRAL INSTITUTION<|>Martin Smith is the Chair of the Central Institution and will answer questions at a press conference<|>9)
<|COMPLETE|>

######################
Example 2:
Text:
TechGlobal's (TG) stock skyrocketed in its opening day on the Global Exchange Thursday. But IPO experts warn that the semiconductor corporation's debut on the public markets isn't indicative of how other newly listed companies may perform.

TechGlobal, a formerly public company, was taken private by Vision Holdings in 2014. The well-established chip designer says it powers 85% of premium smartphones.
######################
Output:
("entity"<|>TECHGLOBAL<|>ORGANIZATION<|>TechGlobal is a stock now listed on the Global Exchange which powers 85% of premium smartphones)
##
("entity"<|>VISION HOLDINGS<|>ORGANIZATION<|>Vision Holdings is a firm that previously owned TechGlobal)
##
("relationship"<|>TECHGLOBAL<|>VISION HOLDINGS<|>Vision Holdings formerly owned TechGlobal from 2014 until present<|>5)
<|COMPLETE|>

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
("entity"<|>FIRUZABAD<|>GEO<|>Firuzabad held Aurelians as hostages)
##
("entity"<|>AURELIA<|>GEO<|>Country seeking to release hostages)
##
("entity"<|>QUINTARA<|>GEO<|>Country that negotiated a swap of money in exchange for hostages)
##
##
("entity"<|>TIRUZIA<|>GEO<|>Capital of Firuzabad where the Aurelians were being held)
##
("entity"<|>KROHAARA<|>GEO<|>Capital city in Quintara)
##
("entity"<|>CASHION<|>GEO<|>Capital city in Aurelia)
##
("entity"<|>SAMUEL NAMARA<|>PERSON<|>Aurelian who spent time in Tiruzia's Alhamia Prison)
##
("entity"<|>ALHAMIA PRISON<|>GEO<|>Prison in Tiruzia)
##
("entity"<|>DURKE BATAGLANI<|>PERSON<|>Aurelian journalist who was held hostage)
##
("entity"<|>MEGGIE TAZBAH<|>PERSON<|>Bratinas national and environmentalist who was held hostage)
##
("relationship"<|>FIRUZABAD<|>AURELIA<|>Firuzabad negotiated a hostage exchange with Aurelia<|>2)
##
("relationship"<|>QUINTARA<|>AURELIA<|>Quintara brokered the hostage exchange between Firuzabad and Aurelia<|>2)
##
("relationship"<|>QUINTARA<|>FIRUZABAD<|>Quintara brokered the hostage exchange between Firuzabad and Aurelia<|>2)
##
("relationship"<|>SAMUEL NAMARA<|>ALHAMIA PRISON<|>Samuel Namara was a prisoner at Alhamia prison<|>8)
##
("relationship"<|>SAMUEL NAMARA<|>MEGGIE TAZBAH<|>Samuel Namara and Meggie Tazbah were exchanged in the same hostage release<|>2)
##
("relationship"<|>SAMUEL NAMARA<|>DURKE BATAGLANI<|>Samuel Namara and Durke Bataglani were exchanged in the same hostage release<|>2)
##
("relationship"<|>MEGGIE TAZBAH<|>DURKE BATAGLANI<|>Meggie Tazbah and Durke Bataglani were exchanged in the same hostage release<|>2)
##
("relationship"<|>SAMUEL NAMARA<|>FIRUZABAD<|>Samuel Namara was a hostage in Firuzabad<|>2)
##
("relationship"<|>MEGGIE TAZBAH<|>FIRUZABAD<|>Meggie Tazbah was a hostage in Firuzabad<|>2)
##
("relationship"<|>DURKE BATAGLANI<|>FIRUZABAD<|>Durke Bataglani was a hostage in Firuzabad<|>2)
<|COMPLETE|>

######################
-Real Data-
######################
Text: {input_text}
######################
Output:
"""
