from typing import List

from pydantic import BaseModel


class TokenResponse(BaseModel):
    token: str
    spacy_pos: str
    matched_forms: List[str]
