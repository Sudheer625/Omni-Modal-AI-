from typing import List, Optional

from llm_client import OpenRouterClient


SUMMARY_HINTS = ("summar", "main point", "key point", "brief", "outline", "tl;dr")


def chunk_text(text: str, chunk_size_words: int = 500, overlap_words: int = 75) -> List[str]:
    words = text.split()
    if not words:
        return []

    step = max(1, chunk_size_words - overlap_words)
    chunks = []
    for i in range(0, len(words), step):
        window = words[i : i + chunk_size_words]
        if window:
            chunks.append(" ".join(window))
    return chunks


class FusionEngine:
    def __init__(self, llm_client: OpenRouterClient) -> None:
        self.llm_client = llm_client

    def generate_answer(
        self,
        question: str,
        image_descriptions: Optional[List[str]] = None,
        document_chunks: Optional[List[str]] = None,
    ) -> str:
        context_sections = []

        if image_descriptions:
            image_context = "\n\n".join(image_descriptions)
            context_sections.append(f"Image Context:\n{image_context}")

        if document_chunks:
            doc_context = "\n\n".join(document_chunks)
            context_sections.append(f"Document Context:\n{doc_context}")

        merged_context = "\n\n".join(context_sections).strip()
        is_summary_request = any(token in question.lower() for token in SUMMARY_HINTS)

        style_instruction = (
            "Format answers in clean markdown with headings and bullet points when useful. "
            "Avoid decorative symbols or noisy separators."
        )
        if is_summary_request:
            style_instruction += (
                " For summaries, provide: 1) Overview, 2) Key Points, 3) Actionable Takeaways if present."
            )

        if merged_context:
            user_prompt = (
                "You MUST answer using the context below. Do not claim you cannot access files.\n"
                "If context is incomplete, say what is missing specifically.\n"
                f"{style_instruction}\n\n"
                f"Context:\n{merged_context}\n\n"
                f"Question:\n{question}"
            )
        else:
            user_prompt = (
                f"{style_instruction}\n"
                "No file context was provided. Answer normally, and suggest uploading/selecting files when needed.\n"
                f"Question:\n{question}"
            )

        system_prompt = (
            "You are OmniModal AI Assistant. "
            "Provide accurate, concise, and structured answers grounded in available context."
        )
        return self.llm_client.chat(user_prompt, system_prompt=system_prompt)
