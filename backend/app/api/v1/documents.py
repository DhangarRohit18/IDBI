from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, File, Form, Query, UploadFile
from app.config import settings
from app.core.exceptions import ValidationError
from app.dependencies import CurrentActiveUser, DBSession
from app.schemas.common import SuccessResponse, TaskResponse
from app.services.document_service import DocumentService

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}


@router.post("/{msme_id}/upload", response_model=TaskResponse, status_code=202)
async def upload_document(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    fiscal_year: int | None = Form(default=None),
) -> TaskResponse:
    """Upload a financial document for an MSME. Triggers async processing."""
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            detail=f"File type '{file.content_type}' not supported. Allowed: PDF, CSV, XLSX",
        )

    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.max_upload_bytes:
        raise ValidationError(detail=f"File size exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    service = DocumentService(db)
    task_id = await service.process_upload(
        msme_id=msme_id,
        tenant_id=current_user.tenant_id,
        uploaded_by=current_user.id,
        file_content=file_content,
        filename=file.filename or "upload",
        mime_type=file.content_type,
        document_type=document_type,
        fiscal_year=fiscal_year,
        background_tasks=background_tasks,
    )
    return TaskResponse(task_id=task_id, message="Document upload queued for processing")


@router.get("/{msme_id}", summary="List Documents")
async def list_documents(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> list[dict]:
    service = DocumentService(db)
    return await service.list_documents(msme_id, current_user.tenant_id)
