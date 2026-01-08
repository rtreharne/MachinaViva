import os

from pdfminer.high_level import extract_text as pdf_extract
from docx import Document

ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt", ".py"}
MAX_SUBMISSION_TEXT_CHARS = 200000


def is_allowed_upload(filename: str) -> bool:
    if not filename:
        return False
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_UPLOAD_EXTENSIONS

def extract_text_from_file(path: str) -> str:
    """Extract text from PDF, DOCX, TXT, or PY."""
    path_lower = path.lower()

    try:
        if path_lower.endswith(".pdf"):
            return pdf_extract(path)

        if path_lower.endswith(".docx"):
            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])

        if path_lower.endswith((".txt", ".py")):
            with open(path, "r", encoding="utf8", errors="replace") as f:
                return f.read()

        return ""
    except Exception as e:
        return f"[Extraction Error: {e}]"
