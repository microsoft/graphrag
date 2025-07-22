# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CFG-based noun phrase extractor."""

from typing import Any

from spacy.tokens.doc import Doc

from graphrag.index.operations.build_noun_graph.np_extractors.base import (
    BaseNounPhraseExtractor,
)
from graphrag.index.operations.build_noun_graph.np_extractors.np_validator import (
    has_valid_token_length,
    is_compound,
    is_valid_entity,
)


class CFGNounPhraseExtractor(BaseNounPhraseExtractor):
    """CFG-based noun phrase extractor."""

    def __init__(
        self,
        model_name: str,
        max_word_length: int,
        include_named_entities: bool,
        exclude_entity_tags: list[str],
        exclude_pos_tags: list[str],
        exclude_nouns: list[str],
        word_delimiter: str,
        noun_phrase_grammars: dict[tuple, str],
        noun_phrase_tags: list[str],
    ):
        """
        Noun phrase extractor combining CFG-based noun-chunk extraction and NER.

        CFG-based extraction was based on TextBlob's fast NP extractor implementation:
        This extractor tends to be faster than the dependency-parser-based extractors but grammars may need to be changed for different languages.

        Args:
            model_name: SpaCy model name.
            max_word_length: Maximum length (in character) of each extracted word.
            include_named_entities: Whether to include named entities in noun phrases
            exclude_entity_tags: list of named entity tags to exclude in noun phrases.
            exclude_pos_tags: List of POS tags to remove in noun phrases.
            word_delimiter: Delimiter for joining words.
            noun_phrase_grammars: CFG for matching noun phrases.
        """
        super().__init__(
            model_name=model_name,
            max_word_length=max_word_length,
            exclude_nouns=exclude_nouns,
            word_delimiter=word_delimiter,
        )
        self.include_named_entities = include_named_entities
        self.exclude_entity_tags = exclude_entity_tags
        if not include_named_entities:
            self.nlp = self.load_spacy_model(
                model_name, exclude=["lemmatizer", "parser", "ner"]
            )
        else:
            self.nlp = self.load_spacy_model(
                model_name, exclude=["lemmatizer", "parser"]
            )

        self.exclude_pos_tags = exclude_pos_tags
        self.noun_phrase_grammars = noun_phrase_grammars
        self.noun_phrase_tags = noun_phrase_tags

    def extract(
        self,
        text: str,
    ) -> list[str]:
        """
        Extract noun phrases from text. Noun phrases may include named entities and noun chunks, which are filtered based on some heuristics.

        Args:
            text: Text.

        Returns: List of noun phrases.
        """
        doc = self.nlp(text)

        filtered_noun_phrases = set()
        if self.include_named_entities:
            # extract noun chunks + entities then filter overlapping spans
            entities = [
                (ent.text, ent.label_)
                for ent in doc.ents
                if ent.label_ not in self.exclude_entity_tags
            ]
            entity_texts = set({ent[0] for ent in entities})
            cfg_matches = self.extract_cfg_matches(doc)
            noun_phrases = entities + [
                np for np in cfg_matches if np[0] not in entity_texts
            ]

            # filter noun phrases based on heuristics
            tagged_noun_phrases = [
                self._tag_noun_phrases(np, entity_texts) for np in noun_phrases
            ]
            for tagged_np in tagged_noun_phrases:
                if (tagged_np["is_valid_entity"]) or (
                    (
                        len(tagged_np["cleaned_tokens"]) > 1
                        or tagged_np["has_compound_words"]
                    )
                    and tagged_np["has_valid_tokens"]
                ):
                    filtered_noun_phrases.add(tagged_np["cleaned_text"])
        else:
            noun_phrases = self.extract_cfg_matches(doc)
            tagged_noun_phrases = [self._tag_noun_phrases(np) for np in noun_phrases]
            for tagged_np in tagged_noun_phrases:
                if (tagged_np["has_proper_nouns"]) or (
                    (
                        len(tagged_np["cleaned_tokens"]) > 1
                        or tagged_np["has_compound_words"]
                    )
                    and tagged_np["has_valid_tokens"]
                ):
                    filtered_noun_phrases.add(tagged_np["cleaned_text"])
        return list(filtered_noun_phrases)

    def extract_cfg_matches(self, doc: Doc) -> list[tuple[str, str]]:
        """Return noun phrases that match a given context-free grammar."""
        tagged_tokens = [
            (token.text, token.pos_)
            for token in doc
            if token.pos_ not in self.exclude_pos_tags
            and token.is_space is False
            and token.text != "-"
        ]
        merge = True
        while merge:
            merge = False
            for index in range(len(tagged_tokens) - 1):
                first, second = tagged_tokens[index], tagged_tokens[index + 1]
                key = first[1], second[1]
                value = self.noun_phrase_grammars.get(key, None)
                if value:
                    # find a matching pattern, pop the two tokens and insert the merged one
                    merge = True
                    tagged_tokens.pop(index)
                    tagged_tokens.pop(index)
                    match = f"{first[0]}{self.word_delimiter}{second[0]}"
                    pos = value
                    tagged_tokens.insert(index, (match, pos))
                    break
        return [t for t in tagged_tokens if t[1] in self.noun_phrase_tags]

    def _tag_noun_phrases(
        self, noun_chunk: tuple[str, str], entities: set[str] | None = None
    ) -> dict[str, Any]:
        """Extract attributes of a noun chunk, to be used for filtering."""
        tokens = noun_chunk[0].split(self.word_delimiter)
        cleaned_tokens = [
            token for token in tokens if token.upper() not in self.exclude_nouns
        ]

        has_valid_entity = False
        if entities and noun_chunk[0] in entities:
            has_valid_entity = is_valid_entity(noun_chunk, cleaned_tokens)

        return {
            "cleaned_tokens": cleaned_tokens,
            "cleaned_text": self.word_delimiter.join(cleaned_tokens)
            .replace("\n", "")
            .upper(),
            "is_valid_entity": has_valid_entity,
            "has_proper_nouns": (noun_chunk[1] == "PROPN"),
            "has_compound_words": is_compound(cleaned_tokens),
            "has_valid_tokens": has_valid_token_length(
                cleaned_tokens, self.max_word_length
            ),
        }

    def __str__(self) -> str:
        """Return string representation of the extractor, used for cache key generation."""
        return f"cfg_{self.model_name}_{self.max_word_length}_{self.include_named_entities}_{self.exclude_entity_tags}_{self.exclude_pos_tags}_{self.exclude_nouns}_{self.word_delimiter}_{self.noun_phrase_grammars}_{self.noun_phrase_tags}"
