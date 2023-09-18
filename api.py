from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models.srt_sentence import SrtSentence

app = FastAPI()


class SentenceRequest(BaseModel):
    sentence: str
    spacy_model: str


@app.post("/process_sentence", response_model=List[str])
async def process_sentence(sentence_request: SentenceRequest):
    try:
        srt_sentence = SrtSentence(
            sentence=sentence_request.sentence, spacy_model=sentence_request.spacy_model
        )
        srt_sentence.clean_get_tokens_and_extract_lexemes()
        if srt_sentence.lexemes:
            return srt_sentence.lexemes
        else:
            raise HTTPException(status_code=400, detail="Error: No lexemes found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
