import logging
import urllib
from typing import List

from pydantic import BaseModel
from spacy.tokens import Token

from models.from_ordia import spacy_token_to_forms

logger = logging.getLogger(__name__)


class LexSrtToken(BaseModel):
    spacy_token: Token
    forms: List[str] = list()
    match_error: bool = False

    class Config:
        arbitrary_types_allowed = True

    def __eq__(self, other):
        """Equal is when the text and PoS from spaCy is the same"""
        return (
                self.text == other.text and self.spacy_lexical_category == other.spacy_lexical_category
        )

    def __hash__(self):
        hash_ = hash(str(self.text + self.spacy_lexical_category))
        # print(hash_)
        return hash_

    @property
    def text(self) -> str:
        return self.spacy_token.text

    @property
    def spacy_lexical_category(self):
        return self.spacy_token.pos_

    def match_against_forms_in_wikidata(self) -> None:
        logger.debug("match_against_forms_in_wikidata: running")
        print("Matching tokes against lexeme forms in Wikidata")
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
            quoted_token_representation = urllib.parse.quote(
                self.spacy_token.norm_.lower()
            )
            # raise MatchError(f"See https://ordia.toolforge.org/search?q={token.norm_.lower()}")
            logger.error(
                f"MatchError: See https://ordia.toolforge.org/search?q={quoted_token_representation}"
            )
            self.match_error = True
        print(f"Found {len(self.forms)} lexemes based on the tokens")

    def match(self, token: Token) -> bool:
        logger.info(
            f"Trying to match '{token.text}' using the spaCy lexical category "
            f"{token.pos_} with lexeme forms in Wikidata"
        )
        forms = spacy_token_to_forms(token=token)
        if forms:
            logger.info(f"Match(es) found {forms}")
            self.forms.extend(forms)
            return True
        else:
            return False

    def match_proper_noun_as_noun(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' in as noun with lexemes " f"in Wikidata"
        )
        forms = spacy_token_to_forms(token=token, lookup_proper_noun_as_noun=True)
        if forms:
            logger.info(
                f"Match(es) found {forms} after forcing the lexical category to noun"
            )
            self.forms.extend(forms)
            return True
        else:
            return False

    def match_proper_noun_as_adjective(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' as adjective with lexemes " f"in Wikidata"
        )
        forms = spacy_token_to_forms(token=token, lookup_proper_noun_as_adjective=True)
        if forms:
            logger.info(f"Match(es) found {forms} after lowercasing")
            self.forms.extend(forms)
            return True
        else:
            return False

    def match_as_noun(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' as noun with lexemes " f"in Wikidata"
        )
        forms = spacy_token_to_forms(token=token, overwrite_as_noun=True)
        if forms:
            logger.info(
                f"Match(es) found {forms} after forcing the lexical category to noun"
            )
            self.forms.extend(forms)
            return True
        else:
            return False

    def match_as_verb(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' as verb with lexemes " f"in Wikidata"
        )
        forms = spacy_token_to_forms(token=token, overwrite_as_verb=True)
        if forms:
            logger.info(
                f"Match(es) found {forms} after forcing the lexical category to verb"
            )
            self.forms.extend(forms)
            return True
        else:
            return False

    def match_as_adjective(self, token: Token):
        logger.info(
            f"Trying to match '{token.text}' as adjective with lexemes " f"in Wikidata"
        )
        forms = spacy_token_to_forms(token=token, overwrite_as_adjective=True)
        if forms:
            logger.info(
                f"Match(es) found {forms} after forcing the lexical category to verb"
            )
            self.forms.extend(forms)
            return True
        else:
            return False

    @property
    def get_as_dictionary(self):
        return {
            "token": self.text,
            "spacy_pos": str(self.spacy_lexical_category),
            "matched_forms": self.forms # this is a list because
                                        # there might be multiple matches
        }