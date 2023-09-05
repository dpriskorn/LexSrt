from typing import List

from pydantic.v1 import validate_arguments
from wikibaseintegrator.entities import LexemeEntity
from wikibaseintegrator.models import Sense

import config
from models.exceptions import MissingInformationError


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def get_cleaned_localized_lemma(lexeme: LexemeEntity) -> str:
    """We shave of the "-" here"""
    return str(lexeme.lemmas.get(language=config.language_code)).replace("-", "")


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def localized_gloss(sense: Sense) -> str:
    if not config.language_code:
        raise MissingInformationError()
    language_value = sense.glosses.get(language=config.language_code)
    if language_value:
        return str(language_value)
    else:
        return (
            f"No gloss for '{config.language_code}' "
            f"language for this sense, please add one"
        )


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def localized_glosses_from_all_senses(lexeme: LexemeEntity) -> List[str]:
    glosses = []
    for sense in lexeme.senses.senses:
        glosses.append(localized_gloss(sense=sense))
    if glosses:
        return glosses
    else:
        return [f"No senses (please help add one here {lexeme.get_entity_url()})"]


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def localized_glosses_as_text(lexeme: LexemeEntity):
    glosses = localized_glosses_from_all_senses(lexeme=lexeme)
    if glosses:
        return " | ".join(glosses)
    else:
        return f"No senses (please help add one)"
