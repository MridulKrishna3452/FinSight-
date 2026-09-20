import base64
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.enums import ImportJobStatus
from app.models.import_job import ImportJob
from app.models.user import User
from app.schemas.import_job import ImportJobRead, ImportPreviewResponse
from app.services.csv_import_service import CSVValidationError, build_preview
from app.workers.tasks import process_csv_import_task

router = APIRouter()

MAX_SIZE_BYTES = settings.CSV_MAX_SIZE_MB * 1024 * 1024


async def _read_and_validate(file: UploadFile) -> bytes:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv files are supported"
        )

    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {settings.CSV_MAX_SIZE_MB}MB",
        )
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")
    return content


@router.post("/csv/preview", response_model=ImportPreviewResponse)
async def preview_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> ImportPreviewResponse:
    content = await _read_and_validate(file)
    try:
        preview_rows, column_map, total_rows = build_preview(content)
    except CSVValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ImportPreviewResponse(
        filename=file.filename or "upload.csv",
        total_rows=total_rows,
        preview_rows=preview_rows,
        detected_columns=column_map,
    )


@router.post("/csv", response_model=ImportJobRead, status_code=status.HTTP_202_ACCEPTED)
async def import_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportJobRead:
    content = await _read_and_validate(file)

    job = ImportJob(
        user_id=current_user.id,
        filename=file.filename or "upload.csv",
        status=ImportJobStatus.QUEUED,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    content_b64 = base64.b64encode(content).decode()
    process_csv_import_task.delay(str(job.id), content_b64)

    return ImportJobRead.model_validate(job)


@router.get("/{job_id}", response_model=ImportJobRead)
def get_import_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportJobRead:
    job = db.get(ImportJob, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return ImportJobRead.model_validate(job)
