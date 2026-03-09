from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from llm_client import LLMClientError
from models.file_model import FileRecord
from models.user_model import UserRecord
from processors import csv_processor, docx_processor, pdf_processor, pptx_processor, xlsx_processor
from processors.image_processor import detect_mime_type, encode_image_to_base64


router = APIRouter(tags=["chat"])


IMAGE_TYPES = {"jpg", "jpeg", "png"}
DOC_TYPES = {"pdf", "docx", "csv", "xlsx", "pptx"}
SUMMARY_HINTS = {
    "summarize",
    "summary",
    "main points",
    "key points",
    "brief",
    "tl;dr",
    "document",
    "file",
    "notes",
    "slide",
    "sheet",
}


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    file_ids: List[int] = Field(default_factory=list)


def _has_file_intent(question: str) -> bool:
    lowered = question.lower()
    return any(token in lowered for token in SUMMARY_HINTS)


def _extract_doc_fallback(file: FileRecord) -> str:
    ext = file.filetype.lower()
    if ext == "pdf":
        return pdf_processor.extract_text(file.filepath)
    if ext == "docx":
        return docx_processor.extract_text(file.filepath)
    if ext == "csv":
        return csv_processor.extract_text(file.filepath)
    if ext == "xlsx":
        return xlsx_processor.extract_text(file.filepath)
    if ext == "pptx":
        return pptx_processor.extract_text(file.filepath)
    return ""


@router.post("/chat")
def chat(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    requested_ids = list(dict.fromkeys(payload.file_ids))
    selected_files: List[FileRecord] = []
    auto_selected = False

    if requested_ids:
        selected_files = (
            db.query(FileRecord)
            .filter(FileRecord.id.in_(requested_ids), FileRecord.owner_id == current_user.id)
            .all()
        )
        found_ids = {record.id for record in selected_files}
        missing = [fid for fid in requested_ids if fid not in found_ids]
        if missing:
            raise HTTPException(status_code=404, detail=f"Files not found: {missing}")

    if not selected_files and _has_file_intent(question):
        recent = (
            db.query(FileRecord)
            .filter(FileRecord.owner_id == current_user.id)
            .order_by(desc(FileRecord.created_at))
            .limit(5)
            .all()
        )
        if recent:
            selected_files = recent
            auto_selected = True

    if not selected_files and _has_file_intent(question):
        return {
            "answer": "Upload a document/image first, or choose files from the manager, and I will summarize them.",
            "used_files": [],
            "auto_selected": False,
            "image_context_count": 0,
            "doc_context_count": 0,
        }

    file_ids = [item.id for item in selected_files]
    image_files = [item for item in selected_files if item.filetype in IMAGE_TYPES]
    doc_files = [item for item in selected_files if item.filetype in DOC_TYPES]

    image_context = []
    doc_context = []

    try:
        for image in image_files:
            encoded = encode_image_to_base64(image.filepath)
            mime_type = detect_mime_type(image.filepath)
            description = request.app.state.llm_client.describe_image(encoded, mime_type)
            image_context.append(f"[{image.filename}]\n{description}")

        if doc_files:
            query_embedding = request.app.state.embedding_engine.embed_query(question)
            doc_ids = [doc.id for doc in doc_files]
            doc_context = request.app.state.vector_store.query(
                query_embedding=query_embedding,
                file_ids=doc_ids,
                top_k=5,
            )

            if not doc_context:
                for doc in doc_files[:3]:
                    extracted = _extract_doc_fallback(doc)
                    if extracted:
                        snippet = extracted[:4000]
                        doc_context.append(f"[{doc.filename}]\n{snippet}")

        answer = request.app.state.fusion_engine.generate_answer(
            question=question,
            image_descriptions=image_context,
            document_chunks=doc_context,
        )

    except LLMClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {exc}") from exc

    return {
        "answer": answer,
        "used_files": file_ids,
        "auto_selected": auto_selected,
        "image_context_count": len(image_context),
        "doc_context_count": len(doc_context),
        "user": current_user.username,
    }
