from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models.file_model import FileRecord, FileResponse, RenameFileRequest
from models.user_model import UserRecord


router = APIRouter(tags=["history"])


@router.get("/files")
def list_files(
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
):
    records = (
        db.query(FileRecord)
        .filter(FileRecord.owner_id == current_user.id)
        .order_by(desc(FileRecord.created_at))
        .all()
    )
    return [FileResponse.model_validate(item).model_dump() for item in records]


@router.put("/files/{file_id}")
def rename_file(
    file_id: int,
    payload: RenameFileRequest,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
):
    record = (
        db.query(FileRecord)
        .filter(FileRecord.id == file_id, FileRecord.owner_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")

    old_path = Path(record.filepath)
    old_extension = old_path.suffix.lower()

    new_name = payload.filename.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Filename cannot be empty.")

    if Path(new_name).suffix.lower() != old_extension:
        new_name = f"{Path(new_name).stem}{old_extension}"

    new_path = old_path.with_name(f"{old_path.stem.split('_', 1)[0]}_{new_name}")

    try:
        old_path.rename(new_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Stored file is missing.") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to rename file: {exc}") from exc

    record.filename = new_name
    record.filepath = str(new_path)
    db.commit()
    db.refresh(record)

    return FileResponse.model_validate(record).model_dump()


@router.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
):
    record = (
        db.query(FileRecord)
        .filter(FileRecord.id == file_id, FileRecord.owner_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")

    request.app.state.vector_store.delete_file_chunks(record.id)

    path = Path(record.filepath)
    if path.exists():
        path.unlink()

    db.delete(record)
    db.commit()

    return {"message": "File deleted successfully.", "id": file_id}
