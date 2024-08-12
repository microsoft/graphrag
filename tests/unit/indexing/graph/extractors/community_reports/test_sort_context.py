# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import math
import platform

from graphrag.index.graph.extractors.community_reports import sort_context
from graphrag.query.llm.text_utils import num_tokens

nan = math.nan

context: list[dict] = [
    {
        "title": "ALI BABA",
        "degree": 1,
        "node_details": {
            "human_readable_id": 26,
            "title": "ALI BABA",
            "description": "A character from Scrooge's reading, representing a memory of his childhood imagination",
            "degree": 1,
        },
        "edge_details": [
            nan,
            {
                "human_readable_id": 28,
                "source": "SCROOGE",
                "target": "ALI BABA",
                "description": "Scrooge recalls Ali Baba as a fond memory from his childhood readings",
                "rank": 32,
            },
        ],
        "claim_details": [nan],
    },
    {
        "title": "BELLE",
        "degree": 1,
        "node_details": {
            "human_readable_id": 31,
            "title": "BELLE",
            "description": "A woman from Scrooge's past, reflecting on how Scrooge's pursuit of wealth changed him and led to the end of their relationship",
            "degree": 1,
        },
        "edge_details": [
            nan,
            {
                "human_readable_id": 32,
                "source": "SCROOGE",
                "target": "BELLE",
                "description": "Belle and Scrooge were once engaged, but their relationship ended due to Scrooge's growing obsession with wealth",
                "rank": 32,
            },
        ],
        "claim_details": [nan],
    },
    {
        "title": "CHRISTMAS",
        "degree": 1,
        "node_details": {
            "human_readable_id": 17,
            "title": "CHRISTMAS",
            "description": "A festive season that highlights the contrast between abundance and want, joy and misery in the story",
            "degree": 1,
        },
        "edge_details": [
            nan,
            {
                "human_readable_id": 23,
                "source": "SCROOGE",
                "target": "CHRISTMAS",
                "description": "Scrooge's disdain for Christmas is a central theme, highlighting his miserliness and lack of compassion",
                "rank": 32,
            },
        ],
        "claim_details": [nan],
    },
    {
        "title": "CHRISTMAS DAY",
        "degree": 1,
        "node_details": {
            "human_readable_id": 57,
            "title": "CHRISTMAS DAY",
            "description": "The day Scrooge realizes he hasn't missed the opportunity to celebrate and spread joy",
            "degree": 1,
        },
        "edge_details": [
            nan,
            {
                "human_readable_id": 46,
                "source": "SCROOGE",
                "target": "CHRISTMAS DAY",
                "description": "Scrooge wakes up on Christmas Day with a changed heart, ready to celebrate and spread happiness",
                "rank": 32,
            },
        ],
        "claim_details": [nan],
    },
    {
        "title": "DUTCH MERCHANT",
        "degree": 1,
        "node_details": {
            "human_readable_id": 19,
            "title": "DUTCH MERCHANT",
            "description": "A historical figure mentioned as having built the fireplace in Scrooge's home, adorned with tiles illustrating the Scriptures",
            "degree": 1,
        },
        "edge_details": [
            nan,
            {
                "human_readable_id": 25,
                "source": "SCROOGE",
                "target": "DUTCH MERCHANT",
                "description": "Scrooge's fireplace, built by the Dutch Merchant, serves as a focal point in his room where he encounters Marley's Ghost",
                "rank": 32,
            },
        ],
        "claim_details": [nan],
    },
    {
        "title": "FAN",
        "degree": 1,
        "node_details": {
            "human_readable_id": 27,
            "title": "FAN",
            "description": "Scrooge's sister, who comes to bring him home from school for Christmas, showing a loving family relationship",
            "degree": 1,
        },
        "edge_details": [
            nan,
            {
                "human_readable_id": 29,
                "source": "SCROOGE",
                "target": "FAN",
                "description": "Fan is Scrooge's sister, who shows love and care by bringing him home for Christmas",
                "rank": 32,
            },
        ],
        "claim_details": [nan],
    },
    {
        "title": "FRED",
        "degree": 1,
        "node_details": {
            "human_readable_id": 58,
            "title": "FRED",
            "description": "Scrooge's nephew, who invites Scrooge to Christmas dinner, symbolizing family reconciliation",
            "degree": 1,
        },
        "edge_details": [
            nan,
            {
                "human_readable_id": 47,
                "source": "SCROOGE",
                "target": "FRED",
                "description": "Scrooge accepts Fred's invitation to Christmas dinner, marking a significant step in repairing their relationship",
                "rank": 32,
            },
        ],
        "claim_details": [nan],
    },
    {
        "title": "GENTLEMAN",
        "degree": 1,
        "node_details": {
            "human_readable_id": 15,
            "title": "GENTLEMAN",
            "description": "Represents charitable efforts to provide for the poor during the Christmas season",
            "degree": 1,
        },
        "edge_details": [
            nan,
            {
                "human_readable_id": 21,
                "source": "SCROOGE",
                "target": "GENTLEMAN",
                "description": "The gentleman approaches Scrooge to solicit donations for the poor, which Scrooge rebuffs",
                "rank": 32,
            },
        ],
        "claim_details": [nan],
    },
    {
        "title": "GHOST",
        "degree": 1,
        "node_details": {
            "human_readable_id": 25,
            "title": "GHOST",
            "description": "The Ghost is a spectral entity that plays a crucial role in guiding Scrooge through an introspective journey in Charles Dickens' classic tale. This spirit, likely one of the Christmas spirits, takes Scrooge on a transformative voyage through his past memories, the realities of his present, and the potential outcomes of his future. The purpose of this journey is to make Scrooge reflect deeply on his life, encouraging a profound understanding of the joy and meaning of Christmas. By showing Scrooge scenes from his life, including the potential fate of Tiny Tim, the Ghost rebukes Scrooge for his lack of compassion, ultimately aiming to instill in him a sense of responsibility and empathy towards others. Through this experience, the Ghost seeks to enlighten Scrooge, urging him to change his ways for the better.",
            "degree": 1,
        },
        "edge_details": [
            nan,
            {
                "human_readable_id": 27,
                "source": "SCROOGE",
                "target": "GHOST",
                "description": "The Ghost is taking Scrooge on a transformative journey by showing him scenes from his past, aiming to make him reflect on his life choices and their consequences. This spectral guide is not only focusing on Scrooge's personal history but also emphasizing the importance of Christmas and the need for a change in perspective. Through these vivid reenactments, the Ghost highlights the error of Scrooge's ways and the significant impact his actions have on others, including Tiny Tim. This experience is designed to enlighten Scrooge, encouraging him to reconsider his approach to life and the people around him.",
                "rank": 32,
            },
        ],
        "claim_details": [nan],
    },
]


def test_sort_context():
    ctx = sort_context(context)
    assert num_tokens(ctx) == 827 if platform.system() == "Windows" else 826
    assert ctx is not None


def test_sort_context_max_tokens():
    ctx = sort_context(context, max_tokens=800)
    assert ctx is not None
    assert num_tokens(ctx) <= 800
