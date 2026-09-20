import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlertSeverity, AlertType


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    related_transaction_id: uuid.UUID | None
    related_budget_id: uuid.UUID | None
    is_read: bool
    created_at: datetime
