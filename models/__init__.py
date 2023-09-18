import logging
import urllib
from argparse import ArgumentParser
from typing import List

import spacy
from bs4 import BeautifulSoup
from email_validator import EmailNotValidError, validate_email
from pandas import DataFrame
from pydantic import BaseModel
from spacy.tokens import Token
from srt import parse  # type: ignore
from wikibaseintegrator import WikibaseIntegrator  # type: ignore
from wikibaseintegrator.entities import LexemeEntity  # type: ignore
from wikibaseintegrator.wbi_config import config as wbi_config  # type: ignore

import config
from models.exceptions import LanguageCodeError
from models.srt_lexeme_entity import SrtLexemeEntity
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
    forms: List[str] = list()
    tokens_above_minimum_length: List[LexSrtToken] = list()
    unique_wbi_lexemes: List[LexemeEntity] = list()
    lexeme_dataframe: DataFrame = DataFrame()
    match_error_dataframe: DataFrame = DataFrame()
    language_code: str = ""
    spacy_model: str = ""
    encoding: str = "utf-8"

    class Config:
        arbitrary_types_allowed = True

    def start(self):
        self.setup_argparse_and_get_filename()
        self.check_language_code()
        self.read_srt_file()
        self.get_srt_content_and_remove_commercial()
        self.get_spacy_tokens()
        self.extract_lexemes_based_on_tokens()
        self.get_unique_wbi_lexemes()
        self.print_all_unique_wbi_lexemes()
        self.print_number_of_unique_lexemes_with_no_senses()
        self.create_lexeme_dataframe()
        self.create_match_error_dataframe()
        self.write_to_csv()

    def check_language_code(self):
        if not 2 <= len(self.language_code) <= 3:
            raise LanguageCodeError(
                "The language code was not a supported length of 2-3 characters"
            )

    def read_srt_file(self):
        """Open and read the SRT file with a specific encoding (e.g., 'latin-1')"""
        try:
            with open(self.filename, encoding=self.encoding) as file:
                self.srt_lines = file.read()
        except UnicodeDecodeError:
            print(
                f"Failed to decode the file using '{self.encoding}' encoding. "
                f"Try adding --encoding 'latin-1' to the command line"
            )

    def setup_argparse_and_get_filename(self):
        parser = ArgumentParser(
            description="Read and process SRT files from the command line."
        )
        parser.add_argument(
            "--file-encoding",
            required=False,
            help="Force a certain file encoding of the SRT file, e.g. 'latin-1'",
            default="utf-8",
        )
        parser.add_argument("-i", "--input", required=True, help="Input SRT file name")
        parser.add_argument(
            "-l", "--lang", required=True, help="Wikimedia supported language code"
        )
        parser.add_argument(
            "-m",
            "--spacy_model",
            required=True,
            help="spaCy NLP language model, e.g. 'en_core_web_sm'",
        )
        args = parser.parse_args()

        self.filename = args.input
        self.language_code = args.lang
        self.spacy_model = args.spacy_model
        self.encoding = args.file_encoding

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
            srt_lexeme = SrtLexemeEntity(
                lexeme=lexeme, language_code=self.language_code
            )
            data.append(
                {
                    "id": lexeme.id,
                    "localized lemma": srt_lexeme.get_cleaned_localized_lemma(),
                    "localized senses": srt_lexeme.localized_glosses_as_text(),
                    "has at least one sense": bool(lexeme.senses),
                    "url": lexeme.get_entity_url(),
                }
            )
        df = DataFrame(data)
        # Sort the DataFrame by the 'localized lemma' column in ascending order
        df_sorted = df.sort_values(by="localized lemma")

        # Optionally, reset the index to have consecutive row numbers
        df_sorted.reset_index(drop=True, inplace=True)

        # Create a DataFrame from the list of dictionaries
        self.lexeme_dataframe = df_sorted

        # debug
        print(self.lexeme_dataframe)

    def create_match_error_dataframe(self):
        data = []

        for token in self.tokens_with_match_error:
            quoted_token_representation = urllib.parse.quote(
                token.spacy_token.norm_.lower()
            )
            data.append(
                {
                    "text": token.text,
                    "ordia url": f"https://ordia.toolforge.org/search?q={quoted_token_representation}",
                    "google url": f"https://google.com?q={quoted_token_representation}",
                }
            )
        df = DataFrame(data)
        # Sort the DataFrame by the 'localized lemma' column in ascending order
        df_sorted = df.sort_values(by="text")

        # Optionally, reset the index to have consecutive row numbers
        df_sorted.reset_index(drop=True, inplace=True)

        # Create a DataFrame from the list of dictionaries
        self.match_error_dataframe = df_sorted

        # debug
        print(self.match_error_dataframe)

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
        print("Tokenizing all subtitle sentences")
        # Load a SpaCy language model (e.g., English)
        nlp = spacy.load(self.spacy_model)

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
            f"Found {len(self.tokenized_sentences)} subtitles "
            f"with a total of {self.number_of_tokens_found} tokens"
        )
        print(
            f"Found {self.count_tokens_above_minimum_length} "
            f"tokens longer than the minimum token "
            f"length ({config.minimum_token_length})"
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
        print("Matching tokes against lexeme forms in Wikidata")
        if self.tokens_above_minimum_length and not self.forms:
            # try deduplicating
            for token in list(set(self.tokens_above_minimum_length)):
                token.convert_token_to_forms()
                if token.forms:
                    self.forms.extend(token.forms)
        print(f"Found {len(self.forms)} forms based on the tokens")

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
        unique_forms = list(set(self.forms))
        print(f"Found {len(unique_forms)} unique lexemes")
        for form in unique_forms:
            wbi_lexeme = wbi.lexeme.get(entity_id=form.split("-")[0])
            self.unique_wbi_lexemes.append(wbi_lexeme)

    def print_all_unique_wbi_lexemes(self):
        logger.debug("print_all_unique_wbi_lexemes: running")
        for wbi_lexeme in self.unique_wbi_lexemes:
            srt_lexeme = SrtLexemeEntity(
                lexeme=wbi_lexeme, language_code=self.language_code
            )
            print(
                f"{srt_lexeme.get_cleaned_localized_lemma()}: "
                f"{srt_lexeme.localized_glosses_as_text()}"
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
            f"{self.number_of_lexemes_with_no_senses} "
            f"lexemes are missing at least one sense"
        )

    def write_to_csv(self):
        if not self.lexeme_dataframe.empty:
            self.lexeme_dataframe.to_csv("lexemes.csv")
        if not self.match_error_dataframe.empty:
            self.match_error_dataframe.to_csv("match_errors.csv")

    @property
    def tokens_with_match_error(self) -> List[LexSrtToken]:
        tokens = []
        for token in self.tokens_above_minimum_length:
            if token.match_error:
                tokens.append(token)
        return tokens
