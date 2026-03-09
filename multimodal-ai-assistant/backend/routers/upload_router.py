from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from auth import get_current_user
from config import ALLOWED_EXTENSIONS, DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES, UPLOADS_DIR
from database import get_db
from fusion_engine import chunk_text
from models.file_model import FileRecord, FileResponse
from models.user_model import UserRecord
from processors import csv_processor, docx_processor, pdf_processor, pptx_processor, xlsx_processor


router = APIRouter(tags=["upload"])


def _extract_document_text(file_path: str, extension: str) -> str:
    if extension == ".pdf":
        return pdf_processor.extract_text(file_path)
    if extension == ".docx":
        return docx_processor.extract_text(file_path)
    if extension == ".csv":
        return csv_processor.extract_text(file_path)
    if extension == ".xlsx":
        return xlsx_processor.extract_text(file_path)
    if extension == ".pptx":
        return pptx_processor.extract_text(file_path)
    return ""


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {extension}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 15MB limit.")

    safe_name = Path(file.filename).name
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    stored_name = f"{timestamp}_{safe_name}"
    stored_path = UPLOADS_DIR / stored_name

    with open(stored_path, "wb") as out:
        out.write(content)

    filetype = extension.lstrip(".")
    record = FileRecord(
        owner_id=current_user.id,
        filename=safe_name,
        filepath=str(stored_path),
        filetype=filetype,
        size=len(content),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    indexed_chunks = 0

    if extension in DOCUMENT_EXTENSIONS:
        extracted_text = _extract_document_text(str(stored_path), extension)
        if extracted_text:
            chunks = chunk_text(extracted_text, chunk_size_words=500, overlap_words=75)
            if chunks:
                embeddings = request.app.state.embedding_engine.embed_texts(chunks)
                request.app.state.vector_store.add_document_chunks(
                    file_id=record.id,
                    filename=record.filename,
                    filetype=record.filetype,
                    chunks=chunks,
                    embeddings=embeddings,
                )
                indexed_chunks = len(chunks)

    return {
        "file": FileResponse.model_validate(record).model_dump(),
        "indexed_chunks": indexed_chunks,
        "is_image": extension in IMAGE_EXTENSIONS,
        "owner": current_user.username,
    }
