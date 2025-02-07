# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing prompts definition."""

COMMUNITY_REPORT_PROMPT = """
You are an AI assistant that helps a human analyst to perform general information discovery.
Information discovery is the process of identifying and assessing relevant information associated with certain entities (e.g., organizations and individuals) within a network.

# Goal
Write a comprehensive report of a community, given a list of entities that belong to the community as well as their relationships and optional associated claims.
The report will be used to inform decision-makers about information associated with the community and their potential impact.
The content of this report includes an overview of the community's key entities, their core attributes or capabilities, their connections, and noteworthy claims.
Retain as much time specific information as possible so your end user can build a timeline of events.

# Report Structure
The report should include the following sections:
- TITLE: community's name that represents its key entities - title should be short but specific. When possible, include representative named entities in the title. Avoid including phrases like 'eligibility assessment' or 'eligibility assessment report' in the title.
- SUMMARY: An executive summary of the community's overall structure, how its entities are related to each other, and significant program-specific or eligibility-related insights.
- IMPORTANCE RATING: A float score between 0-10 that represents the importance of entities within the community..
- RATING EXPLANATION: Give a single sentence explanation of the importance rating.
- DETAILED FINDINGS: A list of 5-10 key insights about the community. Each insight should have a short summary followed by multiple paragraphs of explanatory text grounded according to the grounding rules below. Be comprehensive.
- DATE RANGE: A range of dates (YYYY-MM-DD) with the format [START, END] which corresponds to the date range of text units and intermediate reports used to build the report.

Return output as a well-formed JSON-formatted string with the following format. Don't use any unnecessary escape sequences. The output should be a single JSON object that can be parsed by json.loads.
    {{
        "title": "<report_title>",
        "summary": "<executive_summary>",
        "rating": <importance_rating>,
        "rating_explanation": "<rating_explanation>",
        "findings": [{{"summary":"<insight_1_summary>", "explanation": "<insight_1_explanation"}}, {{"summary":"<insight_2_summary>", "explanation": "<insight_2_explanation"}}],
		"date_range": ["<date range start>", "<date range end>"],

    }}

# Grounding Rules
Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids), <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:
"Person X resolved a major issue with project Y [Data: Sources (1, 5),  Date_Range ((2001, 05, 12), (2001, 05, 14))]. He also made major updates to the database of app Y [Data: Reports (2, 4), Sources (7, 23, 2, 34, 46, +more), Date_Range ((2001, 05, 15), (2001, 05, 18))""

where 1, 2, 4, 5, 7, 23, 2, 34, and 46 represent the id (not the index) of the relevant data record.

# Example Input
-----------
SOURCES
id, text
1, Text: From: compliance.office@enron.com To: management.team@enron.com Cc: legal.team@enron.com, risk@enron.com Date: Wed, 12 Jul 2000 08:30:00 -0600 (CST) Subject: Quick Update on Compliance & Risk Efforts
2, Quick update on what's been cooking in Compliance and Risk Management. Risk Management is stepping up — They've been tightening up on our financial risk assessments and mitigation strategies since early this year.
3, Their efforts are key to keeping us on solid ground financially and in compliance with the latest market regulations as of mid-2000. It's crucial for our strategic planning and helps us stay ahead.
5, Legal's keeping us in check — The Legal Compliance team is on top of ensuring all our operations are up to scratch with legal standards. They're especially focused on improving our corporate governance and contract management as of the second quarter of 2000. This is critical for keeping our operations smooth and legally sound.
9, Working together — Risk Management and Legal Compliance have been syncing up better than ever since the start of Q2 2000. They're making sure our strategies are not just effective but also fully compliant. This coordination is essential for our integrated governance approach.
10, Your thoughts? — How do these updates impact your area? Got ideas on how we can do better? Give your department heads a shout.
11, Thanks for staying engaged. Let's keep pushing for better and smarter ways to work. Cheers, Jane Doe

Output:

{{
    "title": "Enron Compliance and Risk Management Overview as of July 2000",
    "summary": "This report delves into Enron's key departments focusing on compliance and risk management, illustrating how these entities interact within the organizational framework to uphold regulatory standards and manage financial risks effectively. The information is relevant to the company's operations around mid-2000.",
    "rating": 9.2,
    "rating_explanation": "The high importance rating reflects the critical roles that the Risk Management and Legal Compliance Departments play in ensuring Enron's adherence to financial and legal regulations, crucial for maintaining the company's integrity and operational stability.",
    "findings": [
        {{
            "summary": "Risk Management Operational Scope",
            "explanation": "The Risk Management Department at Enron plays a pivotal role in identifying, assessing, and mitigating financial risks. Their proactive approach, highlighted from the beginning of 2000, helps safeguard Enron against potential financial pitfalls and ensures continuous compliance with evolving market regulations. Effective risk management not only prevents financial anomalies but also supports the company's strategic decision-making processes.\n\n[Data: Sources (2, 3), Date_Range ((2000, 01, 01), (2000, 07, 12))]"
        }},
        {{
            "summary": "Legal Compliance and Governance",
            "explanation": "The Legal Compliance Department ensures that all Enron's operations adhere to the legal standards set by regulatory bodies. Their focus on corporate governance and contract management, noted starting Q2 2000, is crucial in maintaining Enron's reputation and operational legality, especially in managing complex contracts and corporate agreements. Their efforts underscore the commitment to upholding high legal standards and ethical practices.\n\n[Data: Source (5), Date_Range ((2000, 04, 01), (2000, 07, 12))]"
        }},
        {{
            "summary": "Interdepartmental Collaboration for Compliance",
            "explanation": "Collaboration between the Risk Management and Legal Compliance Departments, established in Q2 2000, ensures that risk mitigation strategies are legally sound and that compliance measures consider financial risks. This synergy is vital for holistic governance and has been instrumental in integrating risk management with legal compliance strategies at Enron. Enhanced interdepartmental cooperation during this period plays a crucial role in aligning the company's strategies with regulatory requirements.\n\n[Data: Sources (9), Date_Range ((2000, 04, 01), (2000, 07, 12))]"
        }}
    ],
    "date_range": ["2000-01-01", "2000-07-12"]
}}


# Real Data

Use the following text for your answer. Do not make anything up in your answer.

Text:
{input_text}

Output:
"""
