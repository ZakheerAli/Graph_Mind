from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class DocumentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    user_id: str
    title: str
    filename: str
    status: DocumentStatus = DocumentStatus.READY
    page_count: int = 1
    chunk_count: int = 0
    content_snippet: str = ""
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentSummary(BaseModel):
    id: str
    user_id: str
    title: str
    filename: str
    status: DocumentStatus
    page_count: int
    chunk_count: int
    uploaded_at: datetime


class UploadDocumentResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    title: str
    filename: str
