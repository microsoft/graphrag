# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.enums import NounPhraseExtractorType


class TextAnalyzerConfig(BaseModel):
    """Configuration section for NLP text analyzer."""

    extractor_type: NounPhraseExtractorType = Field(
        description="The noun phrase extractor type.",
        default=defs.NLP_EXTRACTOR_TYPE,
    )
    model_name: str = Field(
        description="The SpaCy model name.",
        default=defs.NLP_MODEL_NAME,
    )
    max_word_length: int = Field(
        description="The max word length for NLP parsing.",
        default=defs.NLP_MAX_WORD_LENGTH,
    )
    word_delimiter: str = Field(
        description="The delimiter for splitting words.",
        default=defs.NLP_WORD_DELIMITER,
    )
    include_named_entities: bool = Field(
        description="Whether to include named entities in noun phrases.",
        default=defs.NLP_INCLUDE_NAMED_ENTITIES,
    )
    exclude_nouns: list[str] | None = Field(
        description="The list of excluded nouns (i.e., stopwords). If None, will use a default stopword list",
        default=None,
    )
    exclude_entity_tags: list[str] = Field(
        description="The list of named entity tags to exclude in noun phrases.",
        default=defs.NLP_EXCLUDE_ENTITY_TAGS,
    )
    exclude_pos_tags: list[str] = Field(
        description="The list of part-of-speech tags to remove in noun phrases.",
        default=defs.NLP_EXCLUDE_POS_TAGS,
    )
    noun_phrase_tags: list[str] = Field(
        description="The list of noun phrase tags.",
        default=defs.NLP_NOUN_PHRASE_TAGS,
    )
    noun_phrase_grammars: dict[str, str] = Field(
        description="The CFG for matching noun phrases. The key is a tuple of POS tags and the value is the grammar.",
        default=defs.NLP_NOUN_PHRASE_CFG,
    )


class ExtractGraphNLPConfig(BaseModel):
    """Configuration section for graph extraction via NLP."""

    normalize_edge_weights: bool = Field(
        description="Whether to normalize edge weights.",
        default=defs.NLP_NORMALIZE_EDGE_WEIGHTS,
    )
    text_analyzer: TextAnalyzerConfig = Field(
        description="The text analyzer configuration.", default=TextAnalyzerConfig()
    )
