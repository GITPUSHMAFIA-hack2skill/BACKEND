from __future__ import annotations
import os, uuid
from typing import Dict
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.core.config import settings
from app.schemas import (
    UploadResponse, SummarizeRequest, SummarizeResponse,
    WhatIfRequest, WhatIfResponse, WhatIfItem,
    ClausesRequest, ClausesResponse
)
from app.services import parser
from app.services.summarizer import extractive_summary, LLMClient, abstractive_summary_llm
from app.services.whatif import heuristic_whatif, extract_clauses, whatif_llm

# ---------------- In-memory document store ----------------
class DocumentStore:
    def __init__(self):
        self._docs: Dict[str, Dict] = {}

    def add(self, filename: str, content_type: str, text: str) -> str:
        doc_id = str(uuid.uuid4())
        self._docs[doc_id] = {
            "filename": filename,
            "content_type": content_type,
            "text": text,
            "num_chars": len(text)
        }
        return doc_id

    def get(self, doc_id: str) -> Dict:
        doc = self._docs.get(doc_id)
        if not doc:
            raise KeyError("Not found")
        return doc

STORE = DocumentStore()

# ---------------- App Setup ----------------
app = FastAPI(title="Legal AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_llm() -> LLMClient:
    # Lazy load LLM client so it doesn’t run at startup
    return LLMClient(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        model=settings.OPENAI_MODEL
    )

# ---------------- Routes ----------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "Legal AI Backend is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/documents", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Limit is {settings.MAX_UPLOAD_MB} MB")

    tmp = Path("/tmp") / f"upload_{uuid.uuid4()}{Path(file.filename).suffix}"
    tmp.write_bytes(data)

    try:
        text, ctype = parser.sniff_and_read(tmp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")
    finally:
        tmp.unlink(missing_ok=True)

    doc_id = STORE.add(file.filename, ctype, text)
    return UploadResponse(document_id=doc_id, filename=file.filename, content_type=ctype, num_chars=len(text))

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    try:
        doc = STORE.get(document_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document_id": document_id, **doc}

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest, llm: LLMClient = Depends(get_llm)):
    text = req.text
    if not text and req.document_id:
        try:
            text = STORE.get(req.document_id)["text"]
        except KeyError:
            raise HTTPException(status_code=404, detail="Document not found")
    if not text:
        raise HTTPException(status_code=400, detail="Provide text or document_id")

    if req.mode == "abstractive" and llm.available():
        summ = await abstractive_summary_llm(llm, text)
        return SummarizeResponse(summary=summ, mode="abstractive")

    summ = extractive_summary(text, max_sentences=req.max_sentences)
    return SummarizeResponse(summary=summ, mode="extractive")

@app.post("/whatif", response_model=WhatIfResponse)
async def whatif(req: WhatIfRequest, llm: LLMClient = Depends(get_llm)):
    text = req.text
    if not text and req.document_id:
        try:
            text = STORE.get(req.document_id)["text"]
        except KeyError:
            raise HTTPException(status_code=404, detail="Document not found")
    if not text:
        raise HTTPException(status_code=400, detail="Provide text or document_id")
    if not req.hypotheticals:
        raise HTTPException(status_code=400, detail="Provide at least one hypothetical")

    if llm.available():
        try:
            items = await whatif_llm(llm, text, req.hypotheticals)
            results = [
                WhatIfItem(hypothetical=h, analysis=items[i]["analysis"] if i < len(items) else items[-1]["analysis"])
                for i, h in enumerate(req.hypotheticals)
            ]
            return WhatIfResponse(results=results)
        except Exception:
            pass

    heur = heuristic_whatif(text, req.hypotheticals)
    results = [WhatIfItem(**h) for h in heur]
    return WhatIfResponse(results=results)

@app.post("/clauses", response_model=ClausesResponse)
async def clauses(req: ClausesRequest):
    text = req.text
    if not text and req.document_id:
        try:
            text = STORE.get(req.document_id)["text"]
        except KeyError:
            raise HTTPException(status_code=404, detail="Document not found")
    if not text:
        raise HTTPException(status_code=400, detail="Provide text or document_id")
    return ClausesResponse(clauses=extract_clauses(text))
