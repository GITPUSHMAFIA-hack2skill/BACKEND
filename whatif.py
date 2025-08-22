from __future__ import annotations
from typing import List, Dict
import re
from .summarizer import sentence_split, LLMClient

CLAUSE_HINTS = {
    "payment": r"payment|fee|compensation|invoice|amount|consideration|price|remuneration",
    "liability": r"liabilit|indemnif|damages|hold harmless|limitation of liability|cap",
    "termination": r"terminat|expiry|expire|renewal|notice period|breach",
    "confidentiality": r"confidential|non-disclosure|nda|proprietary|trade secret",
    "ip": r"intellectual property|ip rights|license|licence|ownership|assign",
    "jurisdiction": r"jurisdiction|governing law|venue|dispute|arbitration|forum",
}

def extract_clauses(text: str) -> Dict[str, List[str]]:
    sents = sentence_split(text)
    found = {k: [] for k in CLAUSE_HINTS}
    for s in sents:
        for name, pat in CLAUSE_HINTS.items():
            if re.search(pat, s, flags=re.I):
                found[name].append(s.strip())
    return found

def heuristic_whatif(text: str, hypotheticals: List[str]) -> List[Dict[str, str]]:
    clauses = extract_clauses(text)
    results = []
    for hypo in hypotheticals:
        lower = hypo.lower()
        relevant = []
        if any(k in lower for k in ["pay", "fee", "amount", "price", "invoice", "compensation"]):
            relevant = clauses.get("payment") or []
        elif any(k in lower for k in ["terminat", "extend", "renew", "notice", "breach"]):
            relevant = clauses.get("termination") or []
        elif any(k in lower for k in ["liability", "indemn", "damages", "cap"]):
            relevant = clauses.get("liability") or []
        elif any(k in lower for k in ["confidential", "nda", "secret", "non-disclosure"]):
            relevant = clauses.get("confidentiality") or []
        elif any(k in lower for k in ["jurisdiction", "governing law", "court", "arbitration", "forum"]):
            relevant = clauses.get("jurisdiction") or []
        elif any(k in lower for k in ["ip", "license", "ownership", "assign"]):
            relevant = clauses.get("ip") or []

        analysis = "Based on the current clauses, the hypothetical change may affect the above terms. Review obligations, exceptions, and notice requirements."
        if relevant:
            snippet = "\n- ".join(relevant[:5])
            analysis = f"Likely affected clauses (snippets):\n- {snippet}\n\nImpact (heuristic): {hypo} could trigger renegotiation duties, require written amendments, or change risk allocation. Check conflict/residual clauses."
        results.append({"hypothetical": hypo, "analysis": analysis})
    return results

# ✅ Async LLM-powered what-if
# ✅ Async LLM-powered what-if
async def whatif_llm(llm: LLMClient, text: str, hypotheticals: List[str]) -> List[Dict[str, str]]:
    if not llm.available():
        raise RuntimeError("LLM not configured")

    prompt = [
        {
            "role": "system",
            "content": "You are a contract analyst. Given a contract text and hypotheticals, explain precise impacts, citing relevant clauses and giving risk notes. Keep each answer under ~180 words."
        },
        {
            "role": "user",
            "content": f"""Contract text:
{text[:10000]}

Hypotheticals:
""" + "\n".join(f"- {h}" for h in hypotheticals)
        }
    ]

    out = await llm.chat(prompt, temperature=0.2, max_tokens=1200)

    items = []
    for block in out.split("\n- "):
        block = block.strip().lstrip("- ").strip()
        if not block:
            continue
        items.append({"hypothetical": "", "analysis": block})

    if not items:
        items = [{"hypothetical": h, "analysis": out} for h in hypotheticals]

    return items
