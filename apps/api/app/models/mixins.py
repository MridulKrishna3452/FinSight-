import enum
import uuid
from datetime import datetime
from typing import TypeVar

from sqlalchemy import DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

E = TypeVar("E", bound=enum.Enum)


def pg_enum(enum_cls: type[E], name: str) -> SAEnum:
    """Postgres ENUM column type that stores the Python enum's `.value`
    (e.g. "Groceries") rather than SQLAlchemy's default of the member `.name`
    (e.g. "GROCERIES"), matching the labels created by the Alembic migration."""
    return SAEnum(enum_cls, name=name, values_callable=lambda obj: [e.value for e in obj])


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
