from typing import List, Any

from pydantic import BaseModel
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.datatypes import Lexeme

from models.from_ordia import spacy_token_to_lexemes


class TokenizedSentence(BaseModel):
    sentence: str = ""
    tokens: List[Any] = list()
    lexemes: List[Any] = list()
    wbi: WikibaseIntegrator = WikibaseIntegrator()

    class Config:
        arbitrary_types_allowed = True

    @property
    def number_of_tokens(self) -> int:
        return len(self.tokens)

    def __str__(self) -> str:
        sentences = self.sentence.replace('\n', '')
        if self.tokens:
            return f"Sentence '{sentences}' with {self.number_of_tokens} tokens: {', '.join(self.get_tokens_as_text)}"
        else:
            return f"Sentence '{sentences}' with no tokens detected"

    @property
    def get_tokens_as_text(self) -> List[str]:
        return [token.text for token in self.tokens]

    def convert_tokens_to_lexemes(self):
        """Can we get back multiple lexemes for a single token?"""
        for token in self.tokens:
            lexemes = spacy_token_to_lexemes(token)
            self.lexemes.extend(lexemes)

    def get_wbi_lexemes(self) -> List[Lexeme]:
        return [self.wbi.lexeme.get(entity_id=lexeme) for lexeme in self.lexemes]
