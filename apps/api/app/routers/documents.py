from __future__ import annotations

from fastapi import APIRouter, File, Header, HTTPException, UploadFile

from app.schemas.documents import DocumentSummary, UploadDocumentResponse
from app.services.documents import DocumentService, get_document_service

router = APIRouter()


def get_service() -> DocumentService:
    return get_document_service()


@router.post("/v1/documents", status_code=201, response_model=UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> UploadDocumentResponse:
    user_id = x_user_id or "demo-user"
    service = get_service()
    try:
        contents = await file.read()
        filename = file.filename or "upload.bin"
        document = service.upload_document(filename, contents, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return UploadDocumentResponse(
        document_id=document.id,
        status=document.status,
        title=document.title,
        filename=document.filename,
    )


@router.get("/v1/documents", response_model=list[DocumentSummary])
async def list_documents(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> list[DocumentSummary]:
    user_id = x_user_id or "demo-user"
    service = get_service()
    documents = service.list_documents(user_id)
    return [
        DocumentSummary(
            id=document.id,
            user_id=document.user_id,
            title=document.title,
            filename=document.filename,
            status=document.status,
            page_count=document.page_count,
            chunk_count=document.chunk_count,
            uploaded_at=document.uploaded_at,
        )
        for document in documents
    ]


@router.delete("/v1/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> None:
    user_id = x_user_id or "demo-user"
    service = get_service()
    deleted = service.delete_document(document_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
