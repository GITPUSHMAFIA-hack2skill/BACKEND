from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    content_type: str
    num_chars: int

class SummarizeRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    mode: Literal["extractive","abstractive"] = "extractive"
    max_sentences: int = Field(default=8, ge=3, le=20)

class SummarizeResponse(BaseModel):
    summary: str
    mode: str

class WhatIfRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    hypotheticals: List[str]

class WhatIfItem(BaseModel):
    hypothetical: str
    analysis: str

class WhatIfResponse(BaseModel):
    results: List[WhatIfItem]

class ClausesRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None

class ClausesResponse(BaseModel):
    clauses: dict
