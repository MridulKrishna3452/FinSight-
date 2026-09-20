import { cn } from "@/lib/utils";
import type { Category, TransactionType } from "@/types";

const CATEGORY_COLORS: Record<Category, string> = {
  Housing: "bg-indigo-100 text-indigo-800 dark:bg-indigo-500/20 dark:text-indigo-300",
  Groceries: "bg-lime-100 text-lime-800 dark:bg-lime-500/20 dark:text-lime-300",
  Dining: "bg-orange-100 text-orange-800 dark:bg-orange-500/20 dark:text-orange-300",
  Transport: "bg-sky-100 text-sky-800 dark:bg-sky-500/20 dark:text-sky-300",
  Shopping: "bg-pink-100 text-pink-800 dark:bg-pink-500/20 dark:text-pink-300",
  Entertainment: "bg-purple-100 text-purple-800 dark:bg-purple-500/20 dark:text-purple-300",
  Healthcare: "bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-300",
  Education: "bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-300",
  Utilities: "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300",
  Travel: "bg-teal-100 text-teal-800 dark:bg-teal-500/20 dark:text-teal-300",
  Insurance: "bg-cyan-100 text-cyan-800 dark:bg-cyan-500/20 dark:text-cyan-300",
  Salary: "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300",
  Investments: "bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-300",
  Transfers: "bg-slate-100 text-slate-800 dark:bg-slate-500/20 dark:text-slate-300",
  Other: "bg-gray-100 text-gray-800 dark:bg-gray-500/20 dark:text-gray-300",
};

export function CategoryBadge({ category }: { category: Category | string }) {
  const colorClass = CATEGORY_COLORS[category as Category] ?? CATEGORY_COLORS.Other;
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", colorClass)}>
      {category}
    </span>
  );
}

export function TransactionTypeBadge({ type }: { type: TransactionType }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        type === "income"
          ? "bg-success/15 text-success"
          : "bg-destructive/10 text-destructive",
      )}
    >
      {type === "income" ? "Income" : "Expense"}
    </span>
  );
}
