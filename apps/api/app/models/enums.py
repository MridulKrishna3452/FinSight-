import enum


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Category(str, enum.Enum):
    HOUSING = "Housing"
    GROCERIES = "Groceries"
    DINING = "Dining"
    TRANSPORT = "Transport"
    SHOPPING = "Shopping"
    ENTERTAINMENT = "Entertainment"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    UTILITIES = "Utilities"
    TRAVEL = "Travel"
    INSURANCE = "Insurance"
    SALARY = "Salary"
    INVESTMENTS = "Investments"
    TRANSFERS = "Transfers"
    OTHER = "Other"


class CategorizationSource(str, enum.Enum):
    RULE = "rule"
    USER_OVERRIDE = "user_override"
    FALLBACK = "fallback"


class ImportJobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AlertType(str, enum.Enum):
    SUSPICIOUS_TRANSACTION = "suspicious_transaction"
    BUDGET_THRESHOLD = "budget_threshold"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
