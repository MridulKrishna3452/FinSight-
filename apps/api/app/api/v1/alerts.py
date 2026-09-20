import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertRead

router = APIRouter()


@router.get("", response_model=list[AlertRead])
def list_alerts(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AlertRead]:
    stmt = select(Alert).where(Alert.user_id == current_user.id)
    if unread_only:
        stmt = stmt.where(Alert.is_read.is_(False))
    stmt = stmt.order_by(Alert.created_at.desc())
    alerts = db.execute(stmt).scalars().all()
    return [AlertRead.model_validate(a) for a in alerts]


@router.patch("/{alert_id}/read", response_model=AlertRead)
def mark_alert_read(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertRead:
    alert = db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id)
    ).scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return AlertRead.model_validate(alert)
