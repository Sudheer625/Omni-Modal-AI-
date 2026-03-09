from typing import List

import fitz


def extract_text(pdf_path: str) -> str:
    content: List[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text")
            if text:
                content.append(text)
    return "\n".join(content).strip()
