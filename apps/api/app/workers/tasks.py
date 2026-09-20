import base64
import uuid

from app.core.database import SessionLocal
from app.models.enums import ImportJobStatus
from app.models.import_job import ImportJob
from app.services import csv_import_service
from app.workers.celery_app import celery_app


@celery_app.task(name="process_csv_import")
def process_csv_import_task(job_id: str, content_b64: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(ImportJob, uuid.UUID(job_id))
        if job is None:
            return

        job.status = ImportJobStatus.PROCESSING
        db.commit()

        try:
            content = base64.b64decode(content_b64)
            csv_import_service.process_import(db, job, content)
            job.status = ImportJobStatus.COMPLETED
            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            job = db.get(ImportJob, uuid.UUID(job_id))
            if job is not None:
                job.status = ImportJobStatus.FAILED
                job.error_message = str(exc)[:1000]
                db.commit()
    finally:
        db.close()
