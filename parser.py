from pathlib import Path
from typing import Tuple
from PyPDF2 import PdfReader
from docx import Document

def read_txt(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")

def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks)

def read_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)

def sniff_and_read(path: Path) -> Tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return read_txt(path), "text/plain"
    if suffix == ".pdf":
        return read_pdf(path), "application/pdf"
    if suffix in (".docx", ".doc"):
        # .doc support via python-docx is limited; .doc may fail.
        return read_docx(path), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    raise ValueError(f"Unsupported file type: {suffix}")
