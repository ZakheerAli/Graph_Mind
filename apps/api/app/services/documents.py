from __future__ import annotations

import re
from io import BytesIO
from uuid import uuid4

from app.adapters.document_store import (
    DocumentStore,
    InMemoryDocumentStore,
    PostgresDocumentStore,
)
from app.core.config import Settings, get_settings
from app.schemas.documents import DocumentRecord, DocumentStatus

_in_memory_document_store = InMemoryDocumentStore()


class DocumentService:
    def __init__(self, store: DocumentStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings

    def upload_document(self, filename: str, file_bytes: bytes, user_id: str) -> DocumentRecord:
        if not filename:
            raise ValueError("A file name is required.")

        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in self.settings.allowed_document_types:
            raise ValueError("Unsupported document type.")

        max_bytes = self.settings.max_upload_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise ValueError("File exceeds the upload limit.")

        if self.store.count_for_user(user_id) >= self.settings.max_docs_per_user:
            raise ValueError("User has reached the maximum number of documents.")

        text = extract_text(filename, file_bytes)
        chunks = chunk_text(text)
        document = DocumentRecord(
            id=str(uuid4()),
            user_id=user_id,
            title=filename.rsplit(".", 1)[0] if "." in filename else filename,
            filename=filename,
            status=DocumentStatus.READY,
            page_count=max(1, len(chunks)),
            chunk_count=len(chunks),
            content_snippet=text[:200],
        )
        self.store.add(document, chunks)
        return document

    def list_documents(self, user_id: str) -> list[DocumentRecord]:
        return self.store.list_for_user(user_id)

    def delete_document(self, document_id: str, user_id: str) -> bool:
        return self.store.delete_for_user(document_id, user_id)


def extract_text(filename: str, file_bytes: bytes) -> str:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension in {"txt", "md"}:
        return file_bytes.decode("utf-8", errors="replace")

    if extension == "pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - optional dependency path
            raise ValueError("PDF parsing requires pypdf to be installed.") from exc

        reader = PdfReader(BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    if extension == "docx":
        try:
            from docx import Document
        except ImportError as exc:  # pragma: no cover - optional dependency path
            raise ValueError("DOCX parsing requires python-docx to be installed.") from exc

        doc = Document(BytesIO(file_bytes))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    raise ValueError("Unsupported document type.")


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 80) -> list[str]:
    if not text.strip():
        return [""]

    paragraphs = [segment.strip() for segment in re.split(r"\n\s*\n+", text) if segment.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        normalized = re.sub(r"\s+", " ", paragraph)
        if not normalized:
            continue

        if current and len(current) + 1 + len(normalized) <= chunk_size:
            current = f"{current} {normalized}"
            continue

        if current:
            chunks.append(current)

        if len(normalized) <= chunk_size:
            current = normalized
            continue

        words = normalized.split()
        window: list[str] = []
        for word in words:
            window.append(word)
            if len(" ".join(window)) >= chunk_size:
                chunks.append(" ".join(window))
                window = window[-max(1, overlap // 5) :]
                current = " ".join(window)
                break
        if not current and window:
            current = " ".join(window)

    if current.strip():
        chunks.append(current.strip())

    return [chunk for chunk in chunks if chunk.strip()]


def get_document_service() -> DocumentService:
    settings = get_settings()
    if settings.database_url:
        store: DocumentStore = PostgresDocumentStore(settings.database_url)
    elif settings.app_env == "development":
        store = _in_memory_document_store
    else:
        raise RuntimeError("DATABASE_URL must be configured outside development.")
    return DocumentService(store, settings)
