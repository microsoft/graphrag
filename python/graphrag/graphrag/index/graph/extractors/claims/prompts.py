#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A file containing prompts definition."""

CLAIM_EXTRACTION_PROMPT = """
-Target activity-
You are an intelligent assistant that helps a human analyst to analyze claims against certain entities presented in a text document.

-Goal-
Given a text document that is potentially relevant to this activity, an entity specification, and a claim description, extract all entities that match the entity specification and all claims against those entities.

-Steps-
1. Extract all named entities that match the predefined entity specification. Entity specification can either be a list of entity names or a list of entity types.
2. For each entity identified in step 1, extract all claims associated with the entity. Claims need to match the specified claim description, and the entity should be the subject of the claim.
For each claim, extract the following information:
- Subject: name of the entity that is subject of the claim, capitalized. The subject entity is one that committed the action described in the claim. Subject needs to be one of the named entities identified in step 1.
- Object: name of the entity that is object of the claim, capitalized. The object entity is one that either reports/handles or is affected by the action described in the claim. If object entity is unknown, use **NONE**.
- Claim Type: overall category of the claim, capitalized. Name it in a way that can be repeated across multiple text inputs, so that similar claims share the same claim type
- Claim Status: **TRUE**, **FALSE**, or **SUSPECTED**. TRUE means the claim is confirmed, FALSE means the claim is found to be False, SUSPECTED means the claim is not verified.
- Claim Description: Detailed description explaining the reasoning behind the claim, together with all the related evidence and references.
- Claim Date: Period (start_date, end_date) when the claim was made. Both start_date and end_date should be in ISO-8601 format. If the claim was made on a single date rather than a date range, set the same date for both start_date and end_date. If date is unknown, return **NONE**.
- Claim Source Text: List of **all** quotes from the original text that are relevant to the claim.

Format each claim as (<subject_entity>{tuple_delimiter}<object_entity>{tuple_delimiter}<claim_type>{tuple_delimiter}<claim_status>{tuple_delimiter}<claim_start_date>{tuple_delimiter}<claim_end_date>{tuple_delimiter}<claim_description>{tuple_delimiter}<claim_source>)

3. Return output in English as a single list of all the claims identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

4. When finished, output {completion_delimiter}

-Examples-
Example 1:
Entity specification: organization
Claim description: red flags associated with an entity
Text: According to an article on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B. The company is owned by Person C who was suspected of engaging in corruption activities in 2015.
Output:

(COMPANY A{tuple_delimiter}GOVERNMENT AGENCY B{tuple_delimiter}ANTI-COMPETITIVE PRACTICES{tuple_delimiter}TRUE{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}Company A was found to engage in anti-competitive practices because it was fined for bid rigging in multiple public tenders published by Government Agency B according to an article published on 2022/01/10{tuple_delimiter}According to an article published on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B.)
{completion_delimiter}

Example 2:
Entity specification: Company A, Person C
Claim description: red flags associated with an entity
Text: According to an article on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B. The company is owned by Person C who was suspected of engaging in corruption activities in 2015.
Output:

(COMPANY A{tuple_delimiter}GOVERNMENT AGENCY B{tuple_delimiter}ANTI-COMPETITIVE PRACTICES{tuple_delimiter}TRUE{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}Company A was found to engage in anti-competitive practices because it was fined for bid rigging in multiple public tenders published by Government Agency B according to an article published on 2022/01/10{tuple_delimiter}According to an article published on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B.)
{record_delimiter}
(PERSON C{tuple_delimiter}NONE{tuple_delimiter}CORRUPTION{tuple_delimiter}SUSPECTED{tuple_delimiter}2015-01-01T00:00:00{tuple_delimiter}2015-12-30T00:00:00{tuple_delimiter}Person C was suspected of engaging in corruption activities in 2015{tuple_delimiter}The company is owned by Person C who was suspected of engaging in corruption activities in 2015)
{completion_delimiter}

-Real Data-
Use the following input for your answer.
Entity specification: {entity_specs}
Claim description: {claim_description}
Text: {input_text}
Output:"""

CLAIM_SUMMARY_PROMPT = """
-Target activity-
You are an intelligent assistant that helps a human analyst to process structured records of claims against certain entities.

-Goal-
Given a list of claim records, summarize the records to consolidate duplicated/highly similar records into single records.

-Steps-
1. For each claim record, extract type, status, date, description, source_text and doc_id. Each input claim record is formatted as a dictionary as follows:
    {{
        "covariate_type": "claim"
        "subject_id": "<subject_entity>",
        "subject_type": "entity",
        "object_id": "<object_entity>",
        "object_type": "entity",
        "type": "<claim_group_type>",
        "status": "<claim_group_status>",
        "start_date": "<claim_group_start_date>",
        "end_date": "<claim_group_end_date>",
        "description": "<claim_group_description>",
        "source_text": "<claim_group_source_text>",
        "doc_id": "<claim_group_doc_ids>"
    }}
2. Consolidate records of the same claim types into single claim groups. Each entity may have multiple claim groups.
3. For each group, produce the following fields:
- Subject: name of the entity that is subject of the claim, capitalized.
- Object: name of the entity that is object of the claim, capitalized.
- Type: choose one category that is most representative of all claim types within the group.
- Status: if any records within a group has status = TRUE, set claim_status = TRUE. Otherwise, set claim_status = SUSPECTED.
- Date: if records in the group have different dates, return date range (start_date, end_date). If date is unknown, return **NONE**.
- Description: summarize all claim descriptions of all records within the group into a concise description. Make sure to include information collected from all the descriptions.
- Source text: concatenate all distinct quotes in the source_text fields of all records in the group into a single list of comma-separated strings, e.g. [quote_1, quote_2, ...]
- Doc id: concatenate all distinct doc_ids in the doc_id fields of all records in the group into a single list of comma-separated strings, e.g. [d1,d2, ...]

4. Return output in English as a single list of all the deduplicated claims from step 2 and 3. Format each output claim as (<subject_entity>{tuple_delimiter}<object_entity>{tuple_delimiter}<claim_group_type>{tuple_delimiter}<claim_group_status>{tuple_delimiter}<claim_group_start_date>{tuple_delimiter}<claim_group_end_date>{tuple_delimiter}<claim_group_description>{tuple_delimiter}<claim_group_source_text>{tuple_delimiter}<claim_group_doc_ids>)
Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}


-Examples-
Example 1:
Claim records:
{{
    "subject_id": "COMPANY A",
    "object_id": "GOVERNMENT AGENCY B",
    "type": "ANTI-COMPETITIVE PRACTICES",
    "status": "TRUE",
    "start_date": "2022-01-10T00:00:00",
    "end_date": "2022-01-10T00:00:00",
    "description": "Company A was found to engage in anti-competitive practices because it was fined for bid rigging in multiple public tenders published by Government Agency B according to an article published on 2022/01/10",
    "source_text": ["According to an article published on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B."]
    "doc_id": "d1"
}},
{{
    "subject_id": "COMPANY A",
    "object_id": "GOVERNMENT AGENCY B",
    "type": "ILLEGAL PRACTICES",
    "status": "TRUE",
    "start_date": "2022-01-10T00:00:00",
    "end_date": "2022-01-10T00:00:00",
    "description": "Company A was found to engage in illegal practices because it was fined for bid rigging in multiple public tenders published by Government Agency B according to an article published on 2022/01/10",
    "source_text": ["According to an article published on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B."]
    "doc_id": "d2"
}},
Output:
(COMPANY A{tuple_delimiter}GOVERNMENT AGENCY B{tuple_delimiter}ILLEGAL, ANTI-COMPETITIVE PRACTICES{tuple_delimiter}TRUE{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}2022-01-10T00:00:00{tuple_delimiter}Company A was found to engage in illegal, anti-competitive practices because it was fined for bid rigging in multiple public tenders published by Government Agency B according to an article published on 2022/01/10{tuple_delimiter}According to an article published on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B.{tuple_delimiter}d1,d2)
{completion_delimiter}

-Real Data-
Use the following input for your answer.
Claim records:
{claim_records}
Output:"""


CONTINUE_PROMPT = "MANY entities were missed in the last extraction.  Add them below using the same format:\n"
LOOP_PROMPT = "It appears some entities may have still been missed.  Answer YES {tuple_delimiter} NO if there are still entities that need to be added.\n"
