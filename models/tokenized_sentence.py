from typing import List, Any

from pydantic import BaseModel

from models.from_ordia import spacy_token_to_lexemes


class TokenizedSentence(BaseModel):
    sentence: str = ""
    tokens: List[Any] = list()
    lexemes: List[Any] = list()

    @property
    def number_of_tokens(self) -> int:
        return len(self.tokens)

    def __str__(self) -> str:
        sentences = self.sentence.replace('\n', '')
        if self.tokens:
            return f"Sentence '{sentences}' with {self.number_of_tokens} tokens: {', '.join(self.tokens)}"
        else:
            return f"Sentence '{sentences}' with no tokens detected"

    # def get_tokens_as_text(self):
    #     return [token.text for token in self.tokens]

    def convert_tokens_to_lexemes(self):
        """Can we get back multiple lexemes for a single token?"""
        for token in self.tokens:
            lexemes = spacy_token_to_lexemes(token)
            self.lexemes.extend(lexemes)