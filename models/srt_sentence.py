import logging
from typing import List, Dict

import spacy
from bs4 import BeautifulSoup
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel
from spacy.tokens import Token

import config
from models import LexSrtToken

logger = logging.getLogger(__name__)


class SrtSentence(BaseModel):
    """This class has all logic needed to convert a
    sentence to a list of lexemes in Wikidata

    It deduplicates the tokens before looking up the lexemes
    It only considers lexeme forms when trying to match"""

    sentence: str = ""
    cleaned_sentence: str = ""
    tokens: List[LexSrtToken] = list()
    spacy_model: str = ""

    class Config:
        arbitrary_types_allowed = True

    @property
    def number_of_tokens(self) -> int:
        return len(self.tokens)

    def __str__(self) -> str:
        sentences = self.sentence.replace("\n", "")
        if self.tokens:
            return (
                f"Sentence '{sentences}' with {self.number_of_tokens} "
                f"tokens: {', '.join(self.get_tokens_as_text)}"
            )
        else:
            return f"Sentence '{sentences}' with no tokens detected"

    @property
    def get_tokens_as_text(self) -> List[str]:
        return [token.text for token in self.tokens]

    @property
    def number_of_tokens_longer_than_minimum_length(self) -> int:
        count = 0
        for token in self.tokens:
            if len(token.text) > config.minimum_token_length:
                count += 1
        return count

    def __remove_html_tags__(self):
        # This function removes HTML tags from the given text.
        soup = BeautifulSoup(self.sentence, "html.parser")
        return soup.get_text()

    def __remove_hyphens_not_understood_by_spacy__(self):
        return self.sentence.replace("--", "")

    def __extract_clean_sentence__(self):
        self.cleaned_sentence = self.sentence
        self.cleaned_sentence = self.__remove_html_tags__()
        self.cleaned_sentence = self.__remove_hyphens_not_understood_by_spacy__()

    @property
    def valid_email(self) -> bool:
        try:
            # Check that the email address is valid. Turn on check_deliverability
            # for first-time validations like on account creation pages (but not
            # login pages).
            validate_email(self.sentence, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False

    def __get_spacy_tokens__(self):
        logger.debug("get_spacy_tokens: running")
        print("Tokenizing all subtitle sentences")
        # Load a SpaCy language model (e.g., English)
        nlp = spacy.load(self.spacy_model)

        sentence = self.cleaned_sentence
        doc = nlp(sentence)
        tokens = [token for token in doc]
        filtered_tokens = self.__filter_tokens__(tokens)
        self.tokens = self.convert_to_lexsrttoken(filtered_tokens)

    def __match_forms_based_on_tokens__(self):
        [token.match_against_forms_in_wikidata() for token in self.tokens]

    def clean_get_tokens_and_extract_forms(self):
        """Helper method"""
        self.__extract_clean_sentence__()
        self.__get_spacy_tokens__()
        self.__match_forms_based_on_tokens__()

    def __filter_tokens__(self, tokens):
        """Filter the tokens to remove junk like emails"""
        filtered_tokens = []
        for token in tokens:
            # Filter away emails
            if not self.valid_email:
                filtered_tokens.append(token)
        return filtered_tokens

    @staticmethod
    def convert_to_lexsrttoken(tokens: List[Token]) -> List[LexSrtToken]:
        return [LexSrtToken(spacy_token=token) for token in tokens]

    @property
    def get_dictionaries(self) -> List[Dict[str, str]]:
        dictionaries = [token.get_as_dictionary for token in self.tokens]
        print(dictionaries)
        #exit()
        return [token.get_as_dictionary for token in self.tokens]