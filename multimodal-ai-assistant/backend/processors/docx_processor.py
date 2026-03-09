from typing import List

from docx import Document


def extract_text(docx_path: str) -> str:
    document = Document(docx_path)
    paragraphs: List[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs).strip()
