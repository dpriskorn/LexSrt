from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import JSONResponse

from models.srt_sentence import SrtSentence

app = FastAPI()


class SentenceRequest(BaseModel):
    sentence: str
    spacy_model: str

class IndividualResponse(BaseModel):
    token: str
    spacy_pos: str
    matched_forms: List[str]

class ResponseList(BaseModel):
    data: List[IndividualResponse]

@app.post("/process_sentence", response_model=List[str])
async def process_sentence(sentence_request: SentenceRequest):
    try:
        srt_sentence = SrtSentence(
            sentence=sentence_request.sentence, spacy_model=sentence_request.spacy_model
        )
        srt_sentence.clean_get_tokens_and_extract_forms()
        if srt_sentence.number_of_tokens:
            response_list = [IndividualResponse(**item) for item in srt_sentence.get_dictionaries]
            return JSONResponse(content=ResponseList(data=response_list).model_dump())
        else:
            raise HTTPException(status_code=400, detail="Error: No tokens found by spaCy")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
