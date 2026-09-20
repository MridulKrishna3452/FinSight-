import uuid
from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import CategorizationSource, Category, TransactionType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_category", "user_id", "category"),
        Index("ix_transactions_user_suspicious", "user_id", "is_suspicious"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    transaction_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    merchant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        pg_enum(TransactionType, "transaction_type"), nullable=False
    )
    category: Mapped[Category] = mapped_column(
        pg_enum(Category, "category"), nullable=False, default=Category.OTHER
    )
    categorization_source: Mapped[CategorizationSource] = mapped_column(
        pg_enum(CategorizationSource, "categorization_source"),
        nullable=False,
        default=CategorizationSource.FALLBACK,
    )
    payment_method: Mapped[str] = mapped_column(String(100), nullable=False, default="Other")
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0, nullable=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_explanation: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dedup_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    import_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_jobs.id", ondelete="SET NULL"), nullable=True
    )
