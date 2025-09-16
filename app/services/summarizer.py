from __future__ import annotations
from typing import List, Optional, Dict
import re
import math
import nltk
from collections import Counter
import os

NLTK_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'nltk_data'))
nltk.data.path.append(NLTK_DATA_PATH)

# Now import or use NLTK as usual
# from nltk.tokenize import sent_tokenize


def sentence_split(text: str) -> List[str]:
    from nltk.tokenize import sent_tokenize
    sents = [s.strip() for s in sent_tokenize(text) if s.strip()]
    return sents

STOPWORDS = set('''a an the and or but if while with without to from by for of on in into at over under above below is are was were be being been am do does did doing have has had having this that those these as it its their his her hers them they you your i me my we our us not no nor can could should would may might will shall must'''.split())

def normalize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z']+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

def extractive_summary(text: str, max_sentences: int = 7) -> str:
    sents = sentence_split(text)
    if not sents:
        return ""
    # word frequency scoring
    word_freq = Counter()
    for s in sents:
        word_freq.update(normalize(s))

    if not word_freq:
        return " ".join(sents[:max_sentences])

    # sentence scores (add position bonus)
    scores = []
    for idx, s in enumerate(sents):
        words = normalize(s)
        score = sum(word_freq[w] for w in words) / (len(words) + 1e-6)
        # slight bonus for earlier sentences
        score *= 1.0 + 0.1 * math.exp(-idx / max(1, len(sents)/10))
        scores.append((score, idx, s))

    top = sorted(scores, key=lambda x: x[0], reverse=True)[:max_sentences]
    top_sorted = [s for _, _, s in sorted(top, key=lambda x: x[1])]
    return " ".join(top_sorted)

# ------------------ Optional LLM (OpenAI-compatible) ------------------
import httpx

class LLMClient:
    def __init__(self, api_key: Optional[str], base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model

    def available(self) -> bool:
        return bool(self.api_key)

    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 800) -> str:
        if not self.available():
            raise RuntimeError("LLM not configured")
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

async def abstractive_summary_llm(llm: LLMClient, document_text: str) -> str:
    prompt = [
        {
            "role": "system",
            "content": "You are a legal writing assistant. Produce concise, neutral, layperson-friendly summaries that preserve key obligations, parties, amounts, dates, jurisdiction, and termination terms."
        },
        {
            "role": "user",
            "content": f"""Summarize the following legal document in 8-12 bullet points with short, clear sentences:

{document_text}
"""
        }
    ]
    response = await llm.chat(prompt)
    return response
