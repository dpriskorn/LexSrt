from typing import List

from pydantic import BaseModel
from pydantic.v1 import validate_arguments
from wikibaseintegrator.entities import LexemeEntity  # type: ignore
from wikibaseintegrator.models import Sense  # type: ignore


class SrtLexemeEntity(BaseModel):
    """This code is adapted from LexemeCombinator"""

    lexeme: LexemeEntity
    language_code: str

    class Config:
        arbitrary_types_allowed = True

    def get_cleaned_localized_lemma(self) -> str:
        """We shave of the "-" here"""
        return str(self.lexeme.lemmas.get(language=self.language_code)).replace("-", "")

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def __localized_gloss__(self, sense: Sense) -> str:
        language_value = sense.glosses.get(language=self.language_code)
        if language_value:
            return str(language_value)
        else:
            return (
                f"No gloss for '{self.language_code}' "
                f"language for this sense, please add one"
            )

    def __localized_glosses_from_all_senses__(self) -> List[str]:
        glosses = []
        for sense in self.lexeme.senses.senses:
            glosses.append(self.__localized_gloss__(sense=sense))
        if glosses:
            return glosses
        else:
            return ["No senses (help wanted)"]

    def localized_glosses_as_text(self) -> str:
        glosses = self.__localized_glosses_from_all_senses__()
        if glosses:
            return " | ".join(glosses)
        else:
            return "No senses (please help add one)"
