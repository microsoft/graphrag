MERGE_ENTITIES_SYSTEM = """
You are tasked with analyzing pairs or groups of entities and determining if they should be merged into a single, canonical entity. Your goal is to merge entities that represent the **exact same real-world concept** but differ due to minor linguistic variations.

**Merging Rules:**

1.  **Primary Condition:** Merge only if the entities definitively refer to the *same specific thing* (e.g., the same specific car model, the same person, the same city).
2.  **Allowed Variations for Merging:**
    * **Plural vs. Singular:** e.g., `CAR` vs. `CARS` (if descriptions refer generally), `BUILDING` vs. `BUILDINGS`.
    * **Acronyms vs. Full Names:** e.g., `NYC` vs. `NEW YORK CITY`, `USA` vs. `UNITED STATES OF AMERICA`.
    * **Minor Spelling/Formatting Variations:** e.g., `Dr John Smith` vs. `Dr. John Smith`.
    * **Well-Known Aliases/Nicknames (Use with Caution):** e.g., `THE BIG APPLE` vs. `NEW YORK CITY`, but *only if* descriptions strongly confirm they refer to the identical entity.
    * **Titles/No Titles (for People):** e.g., `PRESIDENT BIDEN` vs. `JOE BIDEN`, *if descriptions confirm it's the same individual*.
3.  **Mandatory Requirements for Merging:**
    * **Identical Type:** The `type` attribute MUST be the same for all entities being merged (e.g., all must be `LOCATION`, or `PERSON`, or `VEHICLE`).
    * **Compatible Descriptions:** The `description` fields must be consistent and describe the same entity. One description might be more detailed, but they should not contradict each other or describe fundamentally different aspects. Merged descriptions should combine the information logically.
4.  **DO NOT MERGE IF:**
    * **Different Types:** e.g., `BERLIN` (LOCATION) vs. `BERLINER` (PERSON or FOOD).
    * **Different Concepts:** Entities represent distinct things, even if related. e.g., `CAR` vs. `TRUCK`, `PARIS` (City) vs. `FRANCE` (Country), `ENGINE` (Component) vs. `CAR` (Vehicle).
    * **Different Specific Entities:** Names are similar but descriptions indicate different individuals, places, or things. e.g., Two people named `John Smith` with different professions described.
    * **Significant Name Differences:** Unless it's a confirmed acronym or very well-known alias with supporting descriptions.
    * **Contradictory Descriptions:** Descriptions point to different characteristics or facts about the entity.

**Output Format:**

If a merge is warranted, output a JSON list containing one object per merge group. Each object should have the following structure:

```json
[{
    "ids": [list_of_original_entity_ids],
    "entities": [list_of_original_entity_names],
    "final_entity": "chosen_canonical_entity_name",
    "final_description": "combined_and_refined_description",
    "final_type": "common_entity_type"
}]'''
If no entities in the input should be merged, output an empty list [].
###
Examples
###
input:
[
  {'entity': 'CAR', 'type': 'VEHICLE', 'description': 'A four-wheeled road vehicle powered by an engine, able to carry a small number of people.', 'id': 10},
  {'entity': 'CARS', 'type': 'VEHICLE', 'description': 'road vehicles designed for transporting people.', 'id': 11}
]
output:
[{
    "ids": [10, 11],
    "entities": ["CAR", "CARS"],
    "final_entity": "CAR", 
    "final_description": "A four-wheeled road vehicle powered by an engine, designed for transporting a small number of people.",
    "final_type": "VEHICLE"
}]
###
input:
[
  {'entity': 'LOS ANGELES', 'type': 'LOCATION', 'description': 'A sprawling Southern California city and the center of the nation’s film and television industry.', 'id': 101},
  {'entity': 'CALIFORNIA', 'type': 'LOCATION', 'description': 'A state in the Western United States, known for its diverse terrain including cliff-lined beaches, redwood forests, the Sierra Nevada Mountains, Central Valley farmland and the Mojave Desert.', 'id': 103},
  {'entity': 'LA', 'type': 'LOCATION', 'description': 'Common abbreviation for Los Angeles, a major city on the Pacific Coast of the USA.', 'id': 102},
  {'entity': 'SAN FRANCISCO', 'type': 'LOCATION', 'description': 'A hilly city on a peninsula between the Pacific Ocean and San Francisco Bay in Northern California.', 'id': 104},
  {'entity': 'HOLLYWOOD SIGN', 'type': 'LANDMARK', 'description': 'An American landmark and cultural icon overlooking Hollywood, Los Angeles, California.', 'id': 105}
]
output:
[{
    "ids": [101, 102],
    "entities": ["LOS ANGELES", "LA"],
    "final_entity": "LOS ANGELES",
    "final_description": "Los Angeles (LA) is a sprawling Southern California city, a major city on the Pacific Coast of the USA, and the center of the nation’s film and television industry.",
    "final_type": "LOCATION"
}]
###
input:
[
  {'entity': 'DR. ANGELA MERKEL', 'type': 'PERSON', 'description': 'German politician who served as Chancellor of Germany from 2005 to 2021. Holds a doctorate in quantum chemistry.', 'id': 30},
  {'entity': 'ANGELA MERKEL', 'type': 'PERSON', 'description': 'Former Chancellor of Germany, leader of the Christian Democratic Union.', 'id': 31},
  {"entity": "BARACK OBAMA","type": "PERSON","description": "44th President of the United States, first African-American president, Nobel Peace Prize laureate.","id": 32}
]
output:
[{
    "ids": [30, 31],
    "entities": ["DR. ANGELA MERKEL", "ANGELA MERKEL"],
    "final_entity": "ANGELA MERKEL", 
    "final_description": "Angela Merkel (Dr.) is a German politician and former Chancellor of Germany (2005-2021), former leader of the Christian Democratic Union, holding a doctorate in quantum chemistry.",
    "final_type": "PERSON"
}]
###
input:
[
  {'entity': 'BERLIN', 'type': 'LOCATION', 'description': 'The capital and largest city of Germany.', 'id': 40},
  {'entity': 'BERLINER', 'type': 'FOOD', 'description': 'A type of German doughnut often filled with jam.', 'id': 41}
]
output:
[]
###
input:
[
  {'entity': 'JOHN SMITH', 'type': 'PERSON', 'description': 'Captain John Smith was an English explorer important to the establishment of Jamestown.', 'id': 50},
  {'entity': 'JOHN SMITH', 'type': 'PERSON', 'description': 'John Smith is a contemporary musician known for his folk guitar style.', 'id': 51}
]
output:
[]

###
input:
[
  {'entity': 'GERMANY', 'type': 'LOCATION', 'description': 'A country in Central Europe, member of the EU.', 'id': 60},
  {'entity': 'BAVARIA', 'type': 'LOCATION', 'description': 'A state (Bundesland) in the southeast of Germany.', 'id': 61}
]
output:
[]
###
"""

MERGE_ENTITIES_INPUT = """
Real input:
{input}
output:
"""

