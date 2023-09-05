import logging
from typing import List

from pydantic import BaseModel
from spacy.tokens import Token
from wikibaseintegrator.entities import LexemeEntity

from models import spacy_token_to_lexemes

logger = logging.getLogger(__name__)


class LexSrtToken(BaseModel):
    spacy_token: Token
    lexemes: List[LexemeEntity] = list()

    class Config:
        arbitrary_types_allowed = True

    def __eq__(self, other):
        """Equal is when the text and PoS from spaCy is the same"""
        return (
            self.text == other.text and self.lexical_category == other.lexical_category
        )

    def __hash__(self):
        hash_ = hash(str(self.text + self.lexical_category))
        # print(hash_)
        return hash_

    @property
    def text(self):
        return self.spacy_token.text

    @property
    def lexical_category(self):
        return self.spacy_token.pos_

    def convert_token_to_lexeme(self) -> None:
        match = self.match(token=self.spacy_token)
        if not match:
            match = self.match_proper_noun_as_noun(token=self.spacy_token)
        if not match:
            match = self.match_proper_noun_as_adjective(token=self.spacy_token)
        if not match:
            match = self.match_as_noun(token=self.spacy_token)
        if not match:
            match = self.match_as_verb(token=self.spacy_token)
        if not match:
            match = self.match_as_adjective(token=self.spacy_token)
        if not match:
            # raise MatchError(f"See https://ordia.toolforge.org/search?q={token.norm_.lower()}")
            logger.error(
                f"MatchError: See https://ordia.toolforge.org/search?q={self.spacy_token.norm_.lower()}"
            )
            input("Continue? (Enter/ctrl + c)")

    def match(self, token: Token) -> bool:
        logger.info(
            f"Trying to match '{token.text}' using the spaCy lexical category "
            f"{token.pos_} with lexemes in Wikidata"
        )
        lexemes = spacy_token_to_lexemes(token=token)
        if lexemes:
            logger.info(f"Match(es) found {lexemes}")
            self.lexemes.extend(lexemes)
            return True
        else:
            return False

    def match_proper_noun_as_noun(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' in as noun with lexemes " f"in Wikidata"
        )
        lexemes = spacy_token_to_lexemes(token=token, lookup_proper_noun_as_noun=True)
        if lexemes:
            logger.info(
                f"Match(es) found {lexemes} after forcing the lexical category to noun"
            )
            self.lexemes.extend(lexemes)
            return True
        else:
            return False

    def match_proper_noun_as_adjective(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' as adjective with lexemes " f"in Wikidata"
        )
        lexemes = spacy_token_to_lexemes(
            token=token, lookup_proper_noun_as_adjective=True
        )
        if lexemes:
            logger.info(f"Match(es) found {lexemes} after lowercasing")
            self.lexemes.extend(lexemes)
            return True
        else:
            return False

    def match_as_noun(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' as noun with lexemes " f"in Wikidata"
        )
        lexemes = spacy_token_to_lexemes(token=token, overwrite_as_noun=True)
        if lexemes:
            logger.info(
                f"Match(es) found {lexemes} after forcing the lexical category to noun"
            )
            self.lexemes.extend(lexemes)
            return True
        else:
            return False

    def match_as_verb(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' as verb with lexemes " f"in Wikidata"
        )
        lexemes = spacy_token_to_lexemes(token=token, overwrite_as_verb=True)
        if lexemes:
            logger.info(
                f"Match(es) found {lexemes} after forcing the lexical category to verb"
            )
            self.lexemes.extend(lexemes)
            return True
        else:
            return False

    def match_as_adjective(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' as adjective with lexemes " f"in Wikidata"
        )
        lexemes = spacy_token_to_lexemes(token=token, overwrite_as_adjective=True)
        if lexemes:
            logger.info(
                f"Match(es) found {lexemes} after forcing the lexical category to verb"
            )
            self.lexemes.extend(lexemes)
            return True
        else:
            return False
