"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

transaction_type_enum = postgresql.ENUM("income", "expense", name="transaction_type", create_type=False)
category_enum = postgresql.ENUM(
    "Housing", "Groceries", "Dining", "Transport", "Shopping", "Entertainment",
    "Healthcare", "Education", "Utilities", "Travel", "Insurance", "Salary",
    "Investments", "Transfers", "Other", name="category", create_type=False,
)
categorization_source_enum = postgresql.ENUM(
    "rule", "user_override", "fallback", name="categorization_source", create_type=False
)
import_job_status_enum = postgresql.ENUM(
    "queued", "processing", "completed", "failed", name="import_job_status", create_type=False
)
alert_type_enum = postgresql.ENUM(
    "suspicious_transaction", "budget_threshold", name="alert_type", create_type=False
)
alert_severity_enum = postgresql.ENUM(
    "info", "warning", "critical", name="alert_severity", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    transaction_type_enum.create(bind, checkfirst=True)
    category_enum.create(bind, checkfirst=True)
    categorization_source_enum.create(bind, checkfirst=True)
    import_job_status_enum.create(bind, checkfirst=True)
    alert_type_enum.create(bind, checkfirst=True)
    alert_severity_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("status", import_job_status_enum, nullable=False, server_default="queued"),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("imported_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duplicate_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("suspicious_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("result_summary", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_import_jobs_user_id", "import_jobs", ["user_id"])

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transaction_date", sa.Date, nullable=False),
        sa.Column("merchant_name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("transaction_type", transaction_type_enum, nullable=False),
        sa.Column("category", category_enum, nullable=False, server_default="Other"),
        sa.Column("categorization_source", categorization_source_enum, nullable=False, server_default="fallback"),
        sa.Column("payment_method", sa.String(100), nullable=False, server_default="Other"),
        sa.Column("is_recurring", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("anomaly_score", sa.Numeric(4, 3), nullable=False, server_default="0"),
        sa.Column("is_suspicious", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("anomaly_explanation", sa.String(500), nullable=True),
        sa.Column("dedup_hash", sa.String(64), nullable=False),
        sa.Column("import_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_dedup_hash", "transactions", ["dedup_hash"])
    op.create_index("ix_transactions_user_date", "transactions", ["user_id", "transaction_date"])
    op.create_index("ix_transactions_user_category", "transactions", ["user_id", "category"])
    op.create_index("ix_transactions_user_suspicious", "transactions", ["user_id", "is_suspicious"])

    op.create_table(
        "budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", category_enum, nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("monthly_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column("year", sa.SmallInteger, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "category", "month", "year", name="uq_budget_user_category_month"),
    )
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", alert_type_enum, nullable=False),
        sa.Column("severity", alert_severity_enum, nullable=False, server_default="info"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.String(1000), nullable=False),
        sa.Column("related_transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("related_budget_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("budgets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("budgets")
    op.drop_table("transactions")
    op.drop_table("import_jobs")
    op.drop_table("refresh_tokens")
    op.drop_table("users")

    bind = op.get_bind()
    alert_severity_enum.drop(bind, checkfirst=True)
    alert_type_enum.drop(bind, checkfirst=True)
    import_job_status_enum.drop(bind, checkfirst=True)
    categorization_source_enum.drop(bind, checkfirst=True)
    category_enum.drop(bind, checkfirst=True)
    transaction_type_enum.drop(bind, checkfirst=True)
