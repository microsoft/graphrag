examples = """
##
Question:
What are the primary functions of actions like bonding and flow in relation to the SI-GC-CU-13 laminate?
##
Answer 1:
The provided data does not contain information about the functions of bonding and flow in relation to the SI-GC-CU-13 laminate.  

The data does provide information about the properties of various laminates, including the SI-GC-CU-13 laminate. However, it does not discuss the specific functions of bonding and flow in relation to this laminate. 

The data does mention that the SI-GC-CU-13 laminate is made of silicone resin, woven glass fabric, and copper conductor [Data: Source unit_text soldering.pdf_13 (13)]. It also provides information about the laminate's thickness, copper weight, and other properties [Data: Source unit_text soldering.pdf_13 (13)]. 

To understand the functions of bonding and flow in relation to the SI-GC-CU-13 laminate, further research would be needed. 
##
Answer 2:
Bonding is a crucial process for creating a strong connection between the different layers of laminate material [Data: Reports (314)].

The flow of solder is also important for ensuring proper wetting of the surface of a component and the printed circuit board [Data: Reports (109)]. This ensures a strong and reliable connection between the component and the board.

The flow of electricity through conductors is influenced by the conductivity of the material [Data: Reports (306)].
##
Answer 3:
The SI-GC-CU-13 laminate is a type of printed circuit board laminate [Data: Entities (324)]. It is a laminate material with a serial number [Data: Entities (324)]. The actions of bonding and flow play a crucial role in creating and maintaining the functionality of this type of laminate. 

**Bonding** refers to the process of connecting layers of laminate materials together [Data: Relationships (314)]. This action is essential in creating multi-layered printed circuit boards, where different layers of laminate are bonded together to create a complex structure [Data: Entities (325)]. In the case of SI-GC-CU-13, bonding helps to create a strong and durable laminate material.

**Flow** is the movement of a substance from one place to another [Data: Entities (156)]. In the context of printed circuit boards, flow refers to the movement of electricity through the circuit [Data: Relationships (316)]. The SI-GC-CU-13 laminate is designed to allow for the flow of electricity, ensuring that the electronic components on the board can communicate and function properly. 

While the data provided does not explicitly state how these actions relate to SI-GC-CU-13, it does provide general information about bonding and flow in printed circuit boards, which is relevant to understanding the functionality of the SI-GC-CU-13 laminate. 
##
Output
[
  {
    "Answer_Number": "1",
    "Comprehensiveness_Reason": "The answer acknowledges that the provided data does not contain information about bonding and flow, but it mentions basic properties of the laminate without further exploration.",
    "Comprehensiveness_Rating": "2",
    "Diversity_Reason": "The answer lacks diversity as it focuses solely on stating the absence of information without adding different angles or explanations related to bonding or flow.",
    "Diversity_Rating": "3",
    "Empowerment_Reason": "The answer does not help the reader make informed judgments since it mostly refers to missing information and suggests further research without any insight into bonding and flow.",
    "Empowerment_Rating": "3",
    "Directness_Reason": "It is direct in acknowledging the lack of information, but it doesn't address the question in a meaningful way.",
    "Directness_Rating": "0"
  },
  {
    "Answer_Number": "2",
    "Comprehensiveness_Reason": "This answer touches on bonding, solder flow, and conductivity, but it is less cohesive and lacks detail compared to Answer 3. It discusses relevant concepts but without directly tying them to the laminate as effectively.",
    "Comprehensiveness_Rating": "6",
    "Diversity_Reason": "It offers a variety of insights by discussing different types of flow (solder and electricity), but the lack of clear connection to the SI-GC-CU-13 laminate limits its diversity.",
    "Diversity_Rating": "6",
    "Empowerment_Reason": "The answer provides some useful information about bonding and solder flow, but its fragmented approach makes it less empowering for the reader compared to Answer 3.",
    "Empowerment_Rating": "6",
    "Directness_Reason": "It somewhat addresses the question but is less focused and direct than Answer 3 in explaining how bonding and flow relate to the SI-GC-CU-13 laminate.",
    "Directness_Rating": "6"
  },
  {
    "Answer_Number": "3",
    "Comprehensiveness_Reason": "This answer provides detailed explanations of bonding and flow, connecting these concepts to printed circuit boards and the SI-GC-CU-13 laminate. It discusses bonding in terms of connecting layers and flow as the movement of electricity.",
    "Comprehensiveness_Rating": "8",
    "Diversity_Reason": "It offers multiple perspectives on bonding (physical connection) and flow (movement of electricity), enriching the reader's understanding of the topic from different angles.",
    "Diversity_Rating": "7",
    "Empowerment_Reason": "The answer empowers the reader by explaining both bonding and flow in the context of PCBs, helping them understand how these concepts apply to the SI-GC-CU-13 laminate.",
    "Empowerment_Rating": "8",
    "Directness_Reason": "It directly addresses the question by explaining the roles of bonding and flow in relation to PCBs and links these actions to the laminate in question.",
    "Directness_Rating": "9"
  }
]
###
Question:
How does soldering potentially contribute to peaceful pursuits?
###
Answer 1:
I cannot answer this question.  The provided text focuses on the technical aspects of soldering in electronics assembly, including its history, methods (hand and machine soldering), and quality control.  There is no information about how soldering contributes to peaceful pursuits.
Output:
[
  {
    "Answer_Number": "1",
    "Comprehensiveness_Reason": "It offers no alternative perspectives or insights.",
    "Comprehensiveness_Rating": "0",
    "Diversity_Reason": "No diversity is present; the response only acknowledges its inability to answer.",
    "Diversity_Rating": "0",
    "Empowerment_Reason": "The answer does not empower the reader; it simply indicates a lack of information and offers no guidance.",
    "Empowerment_Rating": "0",
    "Directness_Reason": "it doesn't address the question in a meaningful way.",
    "Directness_Rating": "0"
  }
]
###

"""

eval_system_prompt ="""
There are three responses to a question You need to rate each answer with a number between 0 to 10 and also provide your reason for the rating.

Negative Points in answers:
- Off-topic or Generalized Content
- Lack of Depth or Detail
- Apologies or Unanswered
- Fragmented or Disorganized
- jumps between topics without clear organization
- Lack of information in text
- Redundancy of information that are not related to the question
- etc
Postive Points in answers:
+ Directly answer the question
+ Avoid superficial and general statements
+ Correct logic in answer related to question
+ Coherence in answer
+ etc

Your output is a list of JSON:
{{
Answer_Number: (str) The number of answer.
Comprehensiveness_Reason: How much detail does the answer provide to cover all aspects and details of the question?
Comprehensiveness_Rating: (str) A rating between 0 to 10
Diversity_Reason: How varied and rich is the answer in providing different perspectives and insights on the question?
Diversity_Rating: (str) A rating between 0 to 10
Empowerment_Reason: How well does the answer help the reader understand and make informed judgements about the topic?
Empowerment_Rating: (str) A rating between 0 to 10
Directness_Reason: How specifically and clearly does the answer address the question?
Directness_Rating: (str) A rating between 0 to 10
}}

## Examples ##
{examples}
## End of Examples ##
""".format(examples=examples)
eval_user_prompt="""
## Real Data ##
##
Question:
{question}
##
Answer 1:
{answer_1}
##
Answer 2:
{answer_2}
##
Answer 3:
{answer_3}
##
Output:
"""


RAG_SYSTEM_PROMPT="""

---Role---

You are a helpful assistant responding to questions about data in the tables provided.


---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.

If you don't know the answer, just say so. Do not make anything up.

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:

"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Sources (15, 16), Reports (1), Entities (5, 7); Relationships (23); Claims (2, 7, 34, 46, 64, +more)]."

where 15, 16, 1, 5, 7, 23, 2, 7, 34, 46, and 64 represent the id (not the index) of the relevant data record.

Do not include information where the supporting evidence for it is not provided.


---Target response length and format---

{response_type}


---Data tables---

{context_data}


---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.

If you don't know the answer, just say so. Do not make anything up.

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:

"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Sources (15, 16), Reports (1), Entities (5, 7); Relationships (23); Claims (2, 7, 34, 46, 64, +more)]."

where 15, 16, 1, 5, 7, 23, 2, 7, 34, 46, and 64 represent the id (not the index) of the relevant data record.

Do NOT include information where the supporting evidence for it is NOT provided. If you can not answer based on the provided text just say so and do not continiue.

---Target response length and format---

{response_type}

Add sections and commentary to the response as appropriate for the length and format. Style the response in markdown.
"""
RESPONSE_TYPE = "multiple paragraphs"