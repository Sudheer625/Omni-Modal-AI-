from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from database import Base


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True, nullable=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(1024), nullable=False)
    filetype = Column(String(50), nullable=False, index=True)
    size = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FileResponse(BaseModel):
    id: int
    owner_id: Optional[int] = None
    filename: str
    filepath: str
    filetype: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True


class RenameFileRequest(BaseModel):
    filename: str
