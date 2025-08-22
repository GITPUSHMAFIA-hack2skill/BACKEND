# Legal AI Backend (FastAPI)

A minimal FastAPI backend that:
- Parses and stores legal documents (PDF/DOCX/TXT).
- Summarizes documents (local extractive *or* LLM if configured).
- Generates "what-if" scenario analyses from the document.
- Provides clean REST endpoints you can plug into any frontend.

## Features
- **Local extractive summarization** (no API keys needed).
- **Optional LLM** via OpenAI-compatible API for higher-quality abstractive summaries and scenario reasoning.
- PDF, DOCX, and TXT support.
- Simple in-memory document store (swap with a DB if needed).

## Endpoints
- `POST /documents` — upload a file; returns a `document_id`.
- `GET /documents/{document_id}` — fetch parsed text metadata.
- `POST /summarize` — summarize raw text or `document_id`.
- `POST /whatif` — generate "what-if" analysis for hypothetical changes.
- `POST /clauses` — extract likely clauses (coarse heuristic) and key entities.

## Quick Start

1) Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```

2) Install dependencies:
```bash
pip install -r requirements.txt
```

3) (Optional) Configure LLM via `.env`:
- Copy `.env.example` to `.env` and set:
```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini   # or any compatible model name
```

4) Run the server:
```bash
uvicorn app.main:app --reload --port 8000
```

5) Open docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Notes
- Local summarizer uses NLTK for sentence splitting + a word-frequency TextRank-style heuristic.
- If LLM is configured, set `mode="abstractive"` in `/summarize` for better results.
- Document storage is **in-memory** for simplicity; replace `DocumentStore` with a DB in production.
- Max file size defaults to ~5 MB (configurable).

## License
MIT
