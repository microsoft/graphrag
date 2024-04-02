# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A file containing prompts definition."""

GRAPH_EXTRACTION_PROMPT = """
-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
 Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>)

3. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

4. When finished, output {completion_delimiter}

######################
-Examples-
######################
Entity_types: ORGANIZATION,PERSON
Text:
The Fed is scheduled to meet on Tuesday and Wednesday, with the central bank planning to release its latest policy decision on Wednesday at 2:00 p.m. ET, followed by a press conference where Fed Chair Jerome Powell will take questions. Investors expect the Federal Open Market Committee to hold its benchmark interest rate steady in a range of 5.25%-5.5%.
######################
Output:
("entity"{tuple_delimiter}FED{tuple_delimiter}ORGANIZATION{tuple_delimiter}The Fed is the Federal Reserve, which is setting interest rates on Tuesday and Wednesday)
{record_delimiter}
("entity"{tuple_delimiter}JEROME POWELL{tuple_delimiter}PERSON{tuple_delimiter}Jerome Powell is the chair of the Federal Reserve)
{record_delimiter}
("entity"{tuple_delimiter}FEDERAL OPEN MARKET COMMITTEE{tuple_delimiter}ORGANIZATION{tuple_delimiter}The Federal Reserve committee makes key decisions about interest rates and the growth of the United States money supply)
{record_delimiter}
("relationship"{tuple_delimiter}JEROME POWELL{tuple_delimiter}FED{tuple_delimiter}Jerome Powell is the Chair of the Federal Reserve and will answer questions at a press conference{tuple_delimiter}9)
{completion_delimiter}
######################
Entity_types: ORGANIZATION
Text:
Arm's (ARM) stock skyrocketed in its opening day on the Nasdaq Thursday. But IPO experts warn that the British chipmaker's debut on the public markets isn't indicative of how other newly listed companies may perform.

Arm, a formerly public company, was taken private by SoftBank in 2016. The well-established chip designer says it powers 99% of premium smartphones.
######################
Output:
("entity"{tuple_delimiter}ARM{tuple_delimiter}ORGANIZATION{tuple_delimiter}Arm is a stock now listed on the Nasdaq which powers 99% of premium smartphones)
{record_delimiter}
("entity"{tuple_delimiter}SOFTBANK{tuple_delimiter}ORGANIZATION{tuple_delimiter}SoftBank is a firm that previously owned Arm)
{record_delimiter}
("relationship"{tuple_delimiter}ARM{tuple_delimiter}SOFTBANK{tuple_delimiter}SoftBank formerly owned Arm from 2016 until present{tuple_delimiter}5)
{completion_delimiter}
######################
Entity_types: ORGANIZATION,GEO,PERSON
Text:
Five Americans jailed for years in Iran and widely regarded as hostages are on their way home to the United States.

The last pieces in a controversial swap mediated by Qatar fell into place when $6bn (£4.8bn) of Iranian funds held in South Korea reached banks in Doha.

It triggered the departure of the four men and one woman in Tehran, who are also Iranian citizens, on a chartered flight to Qatar's capital.

They were met by senior US officials and are now on their way to Washington.

The Americans include 51-year-old businessman Siamak Namazi, who has spent nearly eight years in Tehran's notorious Evin prison, as well as businessman Emad Shargi, 59, and environmentalist Morad Tahbaz, 67, who also holds British nationality.
######################
Output:
("entity"{tuple_delimiter}IRAN{tuple_delimiter}GEO{tuple_delimiter}Iran held American citizens as hostages)
{record_delimiter}
("entity"{tuple_delimiter}UNITED STATES{tuple_delimiter}GEO{tuple_delimiter}Country seeking to release hostages)
{record_delimiter}
("entity"{tuple_delimiter}QATAR{tuple_delimiter}GEO{tuple_delimiter}Country that negotiated a swap of money in exchange for hostages)
{record_delimiter}
("entity"{tuple_delimiter}SOUTH KOREA{tuple_delimiter}GEO{tuple_delimiter}Country holding funds from Iran)
{record_delimiter}
("entity"{tuple_delimiter}TEHRAN{tuple_delimiter}GEO{tuple_delimiter}Capital of Iran where the Iranian hostages were being held)
{record_delimiter}
("entity"{tuple_delimiter}DOHA{tuple_delimiter}GEO{tuple_delimiter}Capital city in Qatar)
{record_delimiter}
("entity"{tuple_delimiter}WASHINGTON{tuple_delimiter}GEO{tuple_delimiter}Capital city in United States)
{record_delimiter}
("entity"{tuple_delimiter}SIAMAK NAMAZI{tuple_delimiter}PERSON{tuple_delimiter}Hostage who spent time in Tehran's Evin prison)
{record_delimiter}
("entity"{tuple_delimiter}EVIN PRISON{tuple_delimiter}GEO{tuple_delimiter}Notorious prison in Tehran)
{record_delimiter}
("entity"{tuple_delimiter}EMAD SHARGI{tuple_delimiter}PERSON{tuple_delimiter}Businessman who was held hostage)
{record_delimiter}
("entity"{tuple_delimiter}MORAD TAHBAZ{tuple_delimiter}PERSON{tuple_delimiter}British national and environmentalist who was held hostage)
{record_delimiter}
("relationship"{tuple_delimiter}IRAN{tuple_delimiter}UNITED STATES{tuple_delimiter}Iran negotiated a hostage exchange with the United States{tuple_delimiter}2)
{record_delimiter}
("relationship"{tuple_delimiter}QATAR{tuple_delimiter}UNITED STATES{tuple_delimiter}Qatar brokered the hostage exchange between Iran and the United States{tuple_delimiter}2)
{record_delimiter}
("relationship"{tuple_delimiter}QATAR{tuple_delimiter}IRAN{tuple_delimiter}Qatar brokered the hostage exchange between Iran and the United States{tuple_delimiter}2)
{record_delimiter}
("relationship"{tuple_delimiter}SIAMAK NAMAZI{tuple_delimiter}EVIN PRISON{tuple_delimiter}Siamak Namazi was a prisoner at Evin prison{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}SIAMAK NAMAZI{tuple_delimiter}MORAD TAHBAZ{tuple_delimiter}Siamak Namazi and Morad Tahbaz were exchanged in the same hostage release{tuple_delimiter}2)
{record_delimiter}
("relationship"{tuple_delimiter}SIAMAK NAMAZI{tuple_delimiter}EMAD SHARGI{tuple_delimiter}Siamak Namazi and Emad Shargi were exchanged in the same hostage release{tuple_delimiter}2)
{record_delimiter}
("relationship"{tuple_delimiter}MORAD TAHBAZ{tuple_delimiter}EMAD SHARGI{tuple_delimiter}Morad Tahbaz and Emad Shargi were exchanged in the same hostage release{tuple_delimiter}2)
{record_delimiter}
("relationship"{tuple_delimiter}SIAMAK NAMAZI{tuple_delimiter}IRAN{tuple_delimiter}Siamak Namazi was a hostage in Iran{tuple_delimiter}2)
{record_delimiter}
("relationship"{tuple_delimiter}MORAD TAHBAZ{tuple_delimiter}IRAN{tuple_delimiter}Morad Tahbaz was a hostage in Iran{tuple_delimiter}2)
{record_delimiter}
("relationship"{tuple_delimiter}EMAD SHARGI{tuple_delimiter}IRAN{tuple_delimiter}Emad Shargi was a hostage in Iran{tuple_delimiter}2)
{completion_delimiter}
######################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:"""

CONTINUE_PROMPT = "MANY entities were missed in the last extraction.  Add them below using the same format:\n"
LOOP_PROMPT = "It appears some entities may have still been missed.  Answer YES | NO if there are still entities that need to be added.\n"
