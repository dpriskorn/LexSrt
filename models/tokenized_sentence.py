import logging
from typing import List

from pydantic import BaseModel
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.entities import LexemeEntity

import config
from models import LexSrtToken

logger = logging.getLogger(__name__)


class TokenizedSentence(BaseModel):
    sentence: str = ""
    tokens: List[LexSrtToken] = list()
    lexemes: List[LexemeEntity] = list()
    wbi: WikibaseIntegrator = WikibaseIntegrator()

    class Config:
        arbitrary_types_allowed = True

    @property
    def number_of_tokens(self) -> int:
        return len(self.tokens)

    def __str__(self) -> str:
        sentences = self.sentence.replace("\n", "")
        if self.tokens:
            return f"Sentence '{sentences}' with {self.number_of_tokens} tokens: {', '.join(self.get_tokens_as_text)}"
        else:
            return f"Sentence '{sentences}' with no tokens detected"

    @property
    def get_tokens_as_text(self) -> List[str]:
        return [token.text for token in self.tokens]

    # def convert_tokens_to_lexemes(self):
    #     """Convert tokens to lexemes if above minimum length"""
    #     for token in self.tokens:
    #         if len(token.text) > config.minimum_token_length:
    #             match = self.match(token=token)
    #             if not match:
    #                 match = self.match_proper_noun_as_noun(token=token)
    #             if not match:
    #                 match = self.match_proper_noun_as_adjective(token=token)
    #             if not match:
    #                 raise MatchError(f"See https://ordia.toolforge.org/search?q={token.norm_.lower()}")
    #                 # logger.error(f"MatchError: See https://ordia.toolforge.org/search?q={token.norm_.lower()}")
    #         else:
    #             logger.debug(f"Discarded short token: {token.text}")

    # def get_wbi_lexemes(self) -> List[Lexeme]:
    #     return [self.wbi.lexeme.get(entity_id=lexeme) for lexeme in self.lexemes]

    @property
    def number_of_tokens_longer_than_minimum_length(self) -> int:
        count = 0
        for token in self.tokens:
            if len(token.text) > config.minimum_token_length:
                count += 1
        return count
