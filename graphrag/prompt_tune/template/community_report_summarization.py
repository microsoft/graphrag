# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Fine-tuning prompts for community report summarization."""

COMMUNITY_REPORT_SUMMARIZATION_PROMPT = """
{persona}

# Goal
Write a comprehensive assessment report of a community taking on the role of a {role}. The content of this report includes an overview of the community's key entities and relationships.

# Report Structure
The report should include the following sections:
- TITLE: community's name that represents its key entities - title should be short but specific. When possible, include representative named entities in the title.
- SUMMARY: An executive summary of the community's overall structure, how its entities are related to each other, and significant points associated with its entities.
- REPORT RATING: {report_rating_description}
- RATING EXPLANATION: Give a single sentence explanation of the rating.
- DETAILED FINDINGS: A list of 5-10 key insights about the community. Each insight should have a short summary followed by multiple paragraphs of explanatory text grounded according to the grounding rules below. Be comprehensive.

Return output as a well-formed JSON-formatted string with the following format. Don't use any unnecessary escape sequences. The output should be a single JSON object that can be parsed by json.loads.
    {{
        "title": "<report_title>",
        "summary": "<executive_summary>",
        "rating": <threat_severity_rating>,
        "rating_explanation": "<rating_explanation>"
        "findings": "[{{"summary":"<insight_1_summary>", "explanation": "<insight_1_explanation"}}, {{"summary":"<insight_2_summary>", "explanation": "<insight_2_explanation"}}]"
    }}

# Grounding Rules
After each paragraph, add data record reference if the content of the paragraph was derived from one or more data records. Reference is in the format of [records: <record_source> (<record_id_list>, ...<record_source> (<record_id_list>)]. If there are more than 10 data records, show the top 10 most relevant records.
Each paragraph should contain multiple sentences of explanation and concrete examples with specific named entities. All paragraphs must have these references at the start and end. Use "NONE" if there are no related roles or records. Everything should be in {language}.

Example paragraph with references added:
This is a paragraph of the output text [records: Entities (1, 2, 3), Claims (2, 5), Relationships (10, 12)]

# Example Input
-----------
Text:

Entities

id,entity,description
5,ABILA CITY PARK,Abila City Park is the location of the POK rally

Relationships

id,source,target,description
37,ABILA CITY PARK,POK RALLY,Abila City Park is the location of the POK rally
38,ABILA CITY PARK,POK,POK is holding a rally in Abila City Park
39,ABILA CITY PARK,POKRALLY,The POKRally is taking place at Abila City Park
40,ABILA CITY PARK,CENTRAL BULLETIN,Central Bulletin is reporting on the POK rally taking place in Abila City Park

Output:
{{
    "title": "Abila City Park and POK Rally",
    "summary": "The community revolves around the Abila City Park, which is the location of the POK rally. The park has relationships with POK, POKRALLY, and Central Bulletin, all
of which are associated with the rally event.",
    "rating": 5.0,
    "rating_explanation": "The impact rating is moderate due to the potential for unrest or conflict during the POK rally.",
    "findings": [
        {{
            "summary": "Abila City Park as the central location",
            "explanation": "Abila City Park is the central entity in this community, serving as the location for the POK rally. This park is the common link between all other
entities, suggesting its significance in the community. The park's association with the rally could potentially lead to issues such as public disorder or conflict, depending on the
nature of the rally and the reactions it provokes. [records: Entities (5), Relationships (37, 38, 39, 40)]"
        }},
        {{
            "summary": "POK's role in the community",
            "explanation": "POK is another key entity in this community, being the organizer of the rally at Abila City Park. The nature of POK and its rally could be a potential
source of threat, depending on their objectives and the reactions they provoke. The relationship between POK and the park is crucial in understanding the dynamics of this community.
[records: Relationships (38)]"
        }},
        {{
            "summary": "POKRALLY as a significant event",
            "explanation": "The POKRALLY is a significant event taking place at Abila City Park. This event is a key factor in the community's dynamics and could be a potential
source of threat, depending on the nature of the rally and the reactions it provokes. The relationship between the rally and the park is crucial in understanding the dynamics of this
community. [records: Relationships (39)]"
        }},
        {{
            "summary": "Role of Central Bulletin",
            "explanation": "Central Bulletin is reporting on the POK rally taking place in Abila City Park. This suggests that the event has attracted media attention, which could
amplify its impact on the community. The role of Central Bulletin could be significant in shaping public perception of the event and the entities involved. [records: Relationships
(40)]"
        }}
    ]

}}

# Real Data

Use the following text for your answer. Do not make anything up in your answer.

Text:
{{input_text}}
Output:"""
