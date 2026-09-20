export const CATEGORIES = [
  "Housing",
  "Groceries",
  "Dining",
  "Transport",
  "Shopping",
  "Entertainment",
  "Healthcare",
  "Education",
  "Utilities",
  "Travel",
  "Insurance",
  "Salary",
  "Investments",
  "Transfers",
  "Other",
] as const;

export type Category = (typeof CATEGORIES)[number];

export type TransactionType = "income" | "expense";
export type CategorizationSource = "rule" | "user_override" | "fallback";
export type ImportJobStatus = "queued" | "processing" | "completed" | "failed";
export type AlertType = "suspicious_transaction" | "budget_threshold";
export type AlertSeverity = "info" | "warning" | "critical";
export type BudgetStatus = "green" | "yellow" | "red";
export type InsightSeverity = "info" | "warning" | "positive";

export interface User {
  id: string;
  email: string;
  full_name: string;
  currency: string;
  is_active: boolean;
}

export interface Transaction {
  id: string;
  transaction_date: string;
  merchant_name: string;
  description: string;
  amount: string;
  transaction_type: TransactionType;
  category: Category;
  categorization_source: CategorizationSource;
  payment_method: string;
  is_recurring: boolean;
  anomaly_score: string;
  is_suspicious: boolean;
  anomaly_explanation: string | null;
  created_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Budget {
  id: string;
  name: string;
  category: Category | null;
  monthly_limit: string;
  month: number;
  year: number;
}

export interface BudgetProgress extends Budget {
  spent: string;
  remaining: string;
  percent_consumed: number;
  status: BudgetStatus;
}

export interface Alert {
  id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  related_transaction_id: string | null;
  related_budget_id: string | null;
  is_read: boolean;
  created_at: string;
}

export interface ImportJob {
  id: string;
  filename: string;
  status: ImportJobStatus;
  total_rows: number;
  imported_rows: number;
  duplicate_rows: number;
  failed_rows: number;
  suspicious_rows: number;
  error_message: string | null;
  result_summary: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ImportPreviewRow {
  row_number: number;
  date: string | null;
  description: string | null;
  amount: string | null;
  type: string | null;
  merchant: string | null;
  payment_method: string | null;
  valid: boolean;
  errors: string[];
}

export interface ImportPreviewResponse {
  filename: string;
  total_rows: number;
  preview_rows: ImportPreviewRow[];
  detected_columns: Record<string, string>;
}

export interface DashboardSummary {
  balance: string;
  monthly_income: string;
  monthly_expense: string;
  savings_rate: number;
  transaction_count: number;
}

export interface CategorySpend {
  category: string;
  total: string;
  percent: number;
  transaction_count: number;
}

export interface MonthlySummaryItem {
  month: string;
  income: string;
  expense: string;
}

export interface DailySpendPoint {
  date: string;
  amount: string;
}

export interface TopMerchant {
  merchant_name: string;
  total: string;
  transaction_count: number;
  category: string;
}

export interface RecurringExpense {
  merchant_name: string;
  category: string;
  average_amount: string;
  occurrences: number;
  last_date: string;
}

export interface ForecastPoint {
  date: string;
  predicted_amount: string;
}

export interface ForecastResponse {
  method: string;
  disclaimer: string;
  historical_daily_average: string;
  points: ForecastPoint[];
}

export interface InsightCard {
  id: string;
  severity: InsightSeverity;
  title: string;
  message: string;
}

export interface InsightsDashboardResponse {
  summary: DashboardSummary;
  spending_by_category: CategorySpend[];
  recent_transactions_count: number;
  insight_cards: InsightCard[];
}
