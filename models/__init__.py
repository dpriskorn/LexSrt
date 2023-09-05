import logging
from argparse import ArgumentParser
from typing import List

import spacy
from bs4 import BeautifulSoup
from email_validator import validate_email, EmailNotValidError
from pandas import DataFrame
from pydantic import BaseModel
from spacy.tokens import Token
from srt import parse
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.entities import LexemeEntity
from wikibaseintegrator.wbi_config import config as wbi_config

import config
from models.exceptions import MatchError
from models.from_lexeme_combinator import (
    localized_glosses_from_all_senses,
    get_cleaned_localized_lemma,
    localized_glosses_as_text,
)
from models.from_ordia import spacy_token_to_lexemes
from models.token import LexSrtToken
from models.tokenized_sentence import TokenizedSentence

logger = logging.getLogger(__name__)
wbi_config["USER_AGENT"] = "LexSrt/1.0 (https://www.wikidata.org/wiki/User:So9q)"
wbi = WikibaseIntegrator()


class LexSrt(BaseModel):
    """
    srt is a bunch of lines read from the file
    # pseudo code
    # accept srt on command line
    # parse srt
    # parse into sentences with tokens
    # extract all tokens
    # remove duplicate tokens
    # filter tokens according to the minimum characters
    # find lexemes for each token
    # output to dataframe
    # export to csv
    """

    srt_lines: str = ""
    srt_contents: List[str] = list()
    tokenized_sentences: List[TokenizedSentence] = list()
    filename: str = ""
    lexemes: List[str] = list()
    tokens_above_minimum_length: List[LexSrtToken] = list()
    unique_wbi_lexemes: List[LexemeEntity] = list()
    lexeme_dataframe: DataFrame = DataFrame()

    class Config:
        arbitrary_types_allowed = True

    def start(self):
        self.setup_argparse_and_get_filename()
        self.read_srt_file()
        self.get_srt_content_and_remove_commercial()
        self.get_spacy_tokens()
        self.extract_lexemes_based_on_tokens()
        self.get_unique_wbi_lexemes()
        self.print_all_unique_wbi_lexemes()
        self.print_number_of_unique_lexemes_with_no_senses()
        self.create_lexeme_dataframe()
        self.write_to_csv()

    def read_srt_file(self):
        # Open and read the SRT file with a specific encoding (e.g., 'latin-1')
        try:
            with open(self.filename, "r", encoding="latin-1") as file:
                self.srt_lines = file.read()
        except UnicodeDecodeError:
            print(
                f"Failed to decode the file using 'latin-1' encoding. Trying 'utf-8'..."
            )

            # If 'latin-1' doesn't work, try 'utf-8'
            with open(self.filename, "r", encoding="utf-8") as file:
                self.srt_lines = file.read()

        # debug
        # if self.srt_lines is not None:
        #     # Process the SRT content here
        #     # You can print it or perform any other actions as needed
        #     print(self.srt_lines)

    def setup_argparse_and_get_filename(self):
        parser = ArgumentParser(
            description="Read and process SRT files from the command line."
        )
        parser.add_argument("-i", "--input", required=True, help="Input SRT file name")
        args = parser.parse_args()

        self.filename = args.input

    def get_srt_content_and_remove_commercial(self):
        """Get the contents as a list of strings"""
        logger.debug("get_srt_content_and_remove_commercial: running")
        # Parse the SRT content into a list of subtitle objects
        subtitles = list(parse(self.srt_lines))

        # Get all the content
        for subtitle in subtitles:
            self.srt_contents.append(subtitle.content)

        # remove commercial
        self.srt_contents = self.srt_contents[:-1]

        # remove credits
        if "subtitles" in str(self.srt_contents[-1:]).lower():
            self.srt_contents = self.srt_contents[:-1]

        if "subtitles" in str(self.srt_contents[-2:-1]).lower():
            self.srt_contents = self.srt_contents[:-2]

        # debug
        # print(self.srt_contents)

    def create_lexeme_dataframe(self):
        data = []

        for lexeme in self.unique_wbi_lexemes:
            data.append(
                {
                    "id": lexeme.id,
                    "localized lemma": get_cleaned_localized_lemma(lexeme=lexeme),
                    "localized senses": localized_glosses_as_text(lexeme=lexeme),
                    "has at least one sense": bool(lexeme.senses),
                    "url": lexeme.get_entity_url(),
                }
            )
        df = DataFrame(data)
        # Sort the DataFrame by the 'localized lemma' column in ascending order
        df_sorted = df.sort_values(by='localized lemma')

        # Optionally, reset the index to have consecutive row numbers
        df_sorted.reset_index(drop=True, inplace=True)

        # Create a DataFrame from the list of dictionaries
        self.lexeme_dataframe = df_sorted

        # debug
        print(self.lexeme_dataframe)

    @staticmethod
    def remove_html_tags(text: str):
        # This function removes HTML tags from the given text.
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text()

    @staticmethod
    def remove_hyphens_not_understood_by_spacy(sentence):
        return sentence.replace("--", "")

    def clean_sentence(self, sentence):
        sentence = self.remove_html_tags(sentence)
        sentence = self.remove_hyphens_not_understood_by_spacy(sentence)
        return sentence

    @staticmethod
    def valid_email(sentence) -> bool:
        try:
            # Check that the email address is valid. Turn on check_deliverability
            # for first-time validations like on account creation pages (but not
            # login pages).
            validate_email(sentence, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False

    def filter_tokens(self, tokens):
        """Filter the tokens to remove junk like emails"""
        filtered_tokens = []
        for token in tokens:
            # Filter away emails
            if not self.valid_email(token.text):
                filtered_tokens.append(token)
        return filtered_tokens

    @staticmethod
    def convert_to_lexsrttoken(tokens: List[Token]) -> List[LexSrtToken]:
        return [LexSrtToken(spacy_token=token) for token in tokens]

    def get_spacy_tokens(self):
        logger.debug("get_spacy_tokens: running")
        # Load a SpaCy language model (e.g., English)
        nlp = spacy.load("en_core_web_sm")

        for sentence in self.srt_contents:
            sentence = self.clean_sentence(sentence)
            doc = nlp(sentence)
            tokens = [token for token in doc]
            filtered_tokens = self.filter_tokens(tokens)
            lexsrttokens = self.convert_to_lexsrttoken(filtered_tokens)
            self.tokenized_sentences.append(
                TokenizedSentence(
                    sentence=sentence,
                    tokens=lexsrttokens,
                    wbi=wbi,
                )
            )
            for token in lexsrttokens:
                if len(token.text) > config.minimum_token_length:
                    self.tokens_above_minimum_length.append(token)

        print(
            f"Found {len(self.tokenized_sentences)} subtitles with a total of {self.number_of_tokens_found} tokens"
        )
        print(
            f"Found {self.count_tokens_above_minimum_length} tokens longer than the minimum token lengh ({config.minimum_token_length})"
        )
        # debug
        # print(f"Number of sentences found: {len(self.tokenized_sentences)}")
        # for ts in self.tokenized_sentences:
        #     print(ts)

    @property
    def count_tokens_above_minimum_length(self) -> int:
        return sum(
            [
                sentence.number_of_tokens_longer_than_minimum_length
                for sentence in self.tokenized_sentences
            ]
        )

    # def extract_lexemes_based_on_sentences(self):
    #     logger.debug("get_lexemes: running")
    #     if not self.lexemes:
    #         for ts in self.tokenized_sentences:
    #             lexemes = ts.convert_tokens_to_lexemes()
    #             if lexemes:
    #                 self.lexemes.extend(lexemes)
    #     print(f"Found {len(self.lexemes)} lexemes based on the tokens")

    # noinspection PyTypeChecker
    def extract_lexemes_based_on_tokens(self):
        logger.debug("extract_lexemes_based_on_tokens: running")
        if self.tokens_above_minimum_length and not self.lexemes:
            # try deduplicating
            for token in list(set(self.tokens_above_minimum_length)):
                token.convert_token_to_lexeme()
                if token.lexemes:
                    self.lexemes.extend(token.lexemes)
        print(f"Found {len(self.lexemes)} lexemes based on the tokens")

    # def get_lexemes_and_print_senses(self):
    #     logger.debug("get_lexeme_ids: running")
    #     for ts in self.tokenized_sentences:
    #         ts.convert_tokens_to_lexemes()
    #         print(ts)
    #         print(f"lexemes: {ts.lexemes}")
    #         for lexeme in ts.get_wbi_lexemes():
    #             lexeme: Lexeme
    #             print(f"{get_cleaned_localized_lemma(lexeme=lexeme)}: "
    #                   f"{localized_glosses_as_text(lexeme=lexeme)}"
    #                   f"\n More details: {lexeme.get_entity_url()}")
    #         exit()

    def get_unique_wbi_lexemes(self):
        logger.debug("get_unique_wbi_lexemes: running")
        unique_lexemes = list(set(self.lexemes))
        print(f"Found {len(unique_lexemes)} unique lexemes")
        for lexeme in unique_lexemes:
            wbi_lexeme = wbi.lexeme.get(entity_id=lexeme)
            self.unique_wbi_lexemes.append(wbi_lexeme)

    def print_all_unique_wbi_lexemes(self):
        logger.debug("print_all_unique_wbi_lexemes: running")
        for wbi_lexeme in self.unique_wbi_lexemes:
            print(
                f"{get_cleaned_localized_lemma(lexeme=wbi_lexeme)}: "
                f"{localized_glosses_as_text(lexeme=wbi_lexeme)}"
                f"\n More details: {wbi_lexeme.get_entity_url()}"
            )

    @property
    def number_of_tokens_found(self) -> int:
        return sum([sentence.number_of_tokens for sentence in self.tokenized_sentences])

    @property
    def number_of_lexemes_with_no_senses(self) -> int:
        count = 0
        for lexeme in self.unique_wbi_lexemes:
            if not lexeme.senses:
                count += 1
        return count

    def print_number_of_unique_lexemes_with_no_senses(self):
        print(
            f"{self.number_of_lexemes_with_no_senses} lexemes are missing at least one sense"
        )

    def write_to_csv(self):
        if not self.lexeme_dataframe.empty:
            self.lexeme_dataframe.to_csv("lexemes.csv")
