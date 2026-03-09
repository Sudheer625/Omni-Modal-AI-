from typing import List

import fitz


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file using PyMuPDF."""
    text_parts = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into approximate token chunks.
    This implementation uses word counts as a practical approximation.
    """
    words = text.split()
    if not words:
        return []

    if overlap >= chunk_size:
        overlap = 0

    step = chunk_size - overlap
    chunks = []

    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        if not chunk_words:
            continue
        chunks.append(" ".join(chunk_words))

    return chunks
