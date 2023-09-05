import logging
from argparse import ArgumentParser
from typing import List

import spacy
from pydantic import BaseModel
from spacy.tokens import Token
from srt import parse
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config

import config
from models.from_lexeme_combinator import localized_glosses_from_all_senses, get_cleaned_localized_lemma, \
    localized_glosses_as_text
from models.tokenized_sentence import TokenizedSentence

logger = logging.getLogger(__name__)
wbi_config['USER_AGENT'] = 'LexSrt/1.0 (https://www.wikidata.org/wiki/User:So9q)'
wbi = WikibaseIntegrator()


class LexSrt(BaseModel):
    """
    srt is a bunch of lines read from the file
    # pseudo code
    # accept srt on command line
    # parse srt
    # parse into tokens
    # find lexemes for each token
    # remove duplicate lexemes
    # remove lexemes less than 5 characters
    # output the list of values needed to find all the senses with WDQS
    """
    srt_lines: str = ""
    srt_contents: List[str] = list()
    tokenized_sentences: List[TokenizedSentence] = list()
    filename: str = ""
    # lines_dataframe: DataFrame = DataFrame()
    # words_dataframe: DataFrame = DataFrame()
    lexemes: List[str] = list()
    tokens_above_minimum_length: List[Token] = list()

    class Config:
        arbitrary_types_allowed = True

    def start(self):
        self.setup_argparse_and_get_filename()
        self.read_srt_file()
        self.get_srt_content_and_remove_commercial()
        self.get_spacy_tokens()
        self.count_tokens_above_minimum_length()
        self.extract_lexemes()
        self.get_lexemes_deduplicate_and_print_all()

    def read_srt_file(self):
        # Open and read the SRT file with a specific encoding (e.g., 'latin-1')
        try:
            with open(self.filename, 'r', encoding='latin-1') as file:
                self.srt_lines = file.read()
        except UnicodeDecodeError:
            print(f"Failed to decode the file using 'latin-1' encoding. Trying 'utf-8'...")

            # If 'latin-1' doesn't work, try 'utf-8'
            with open(self.filename, 'r', encoding='utf-8') as file:
                self.srt_lines = file.read()

        # debug
        # if self.srt_lines is not None:
        #     # Process the SRT content here
        #     # You can print it or perform any other actions as needed
        #     print(self.srt_lines)

    def setup_argparse_and_get_filename(self):
        parser = ArgumentParser(description="Read and process SRT files from the command line.")
        parser.add_argument('-i', '--input', required=True, help="Input SRT file name")
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
        #print(self.srt_contents)

    # def create_dataframes(self):
    #     self.create_lines_dataframe()
    #     self.create_word_dataframe()
    #
    # def create_lines_dataframe(self):
    #     # Create a DataFrame from the list of strings
    #     self.lines_dataframe = DataFrame({'Lines': self.srt_contents})
    #
    # def create_word_dataframe(self):
    #     # Define a regular expression pattern to split text into words while removing punctuation
    #     pattern = r'\b\w+\b'
    #
    #     # Split strings into words, remove punctuation, and convert to lowercase
    #     words = []
    #     for sentence in self.srt_contents:
    #         words.extend(re.findall(pattern, sentence.lower()))
    #
    #     # Deduplicate cleaned words
    #     unique_words = list(set(words))
    #
    #     # Filter out words with fewer than 5 characters
    #     filtered_words = [word for word in unique_words if len(word) >= 5]
    #
    #     # Create a DataFrame
    #     self.words_dataframe = DataFrame({'Words': filtered_words})
    #
    #     # debug
    #     print(self.words_dataframe)

    def get_spacy_tokens(self):
        logger.debug("get_spacy_tokens: running")
        # Load a SpaCy language model (e.g., English)
        nlp = spacy.load("en_core_web_sm")

        for sentence in self.srt_contents:
            doc = nlp(sentence)
            tokens = [token for token in doc]
            # print(sentence, tokens)
            # exit()
            self.tokenized_sentences.append(TokenizedSentence(sentence=sentence, tokens=tokens, wbi=wbi))
            for token in tokens:
                if len(token.text) > config.minimum_token_length:
                    self.tokens_above_minimum_length.append(token)

        print(f"Found {len(self.tokenized_sentences)} subtitles with a total of {self.number_of_tokens_found} tokens")
        # debug
        # print(f"Number of sentences found: {len(self.tokenized_sentences)}")
        # for ts in self.tokenized_sentences:
        #     print(ts)

    def count_tokens_above_minimum_length(self):
        result = sum([sentence.number_of_tokens_longer_than_minimum_length for sentence in self.tokenized_sentences])
        print(f"Found {result} tokens longer than the minimum token lengh ({config.minimum_token_length})")


    def extract_lexemes(self):
        logger.debug("get_lexemes: running")
        if not self.lexemes:
            for ts in self.tokenized_sentences:
                lexemes = ts.convert_tokens_to_lexemes()
                if lexemes:
                    self.lexemes.extend(lexemes)
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

    def get_lexemes_deduplicate_and_print_all(self):
        logger.debug("get_lexemes_deduplicate_and_print_all: running")
        unique_lexemes = list(set(self.lexemes))
        print(f"Found {len(unique_lexemes)} unique lexemes")
        for lexeme in unique_lexemes:
            wbi_lexeme = wbi.lexeme.get(entity_id=lexeme)
            print(f"{get_cleaned_localized_lemma(lexeme=wbi_lexeme)}: "
                  f"{localized_glosses_as_text(lexeme=wbi_lexeme)}"
                  f"\n More details: {wbi_lexeme.get_entity_url()}")
        exit()

    @property
    def number_of_tokens_found(self) -> int:
        return sum([sentence.number_of_tokens for sentence in self.tokenized_sentences])