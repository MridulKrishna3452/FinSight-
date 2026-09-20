import { ArrowDownRight, ArrowUpRight, PiggyBank, Wallet } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";
import type { DashboardSummary } from "@/types";

export function SummaryCards({ summary, currency }: { summary: DashboardSummary; currency: string }) {
  const cards = [
    {
      label: "Balance",
      value: formatCurrency(summary.balance, currency),
      icon: Wallet,
      accent: "text-primary",
    },
    {
      label: "Monthly Income",
      value: formatCurrency(summary.monthly_income, currency),
      icon: ArrowUpRight,
      accent: "text-success",
    },
    {
      label: "Monthly Expense",
      value: formatCurrency(summary.monthly_expense, currency),
      icon: ArrowDownRight,
      accent: "text-destructive",
    },
    {
      label: "Savings Rate",
      value: `${summary.savings_rate.toFixed(1)}%`,
      icon: PiggyBank,
      accent: "text-warning",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.label}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{card.label}</CardTitle>
            <card.icon className={`h-4 w-4 ${card.accent}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
