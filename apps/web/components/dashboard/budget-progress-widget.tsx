"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { EmptyState } from "@/components/shared/state-views";
import { formatCurrency, cn } from "@/lib/utils";
import { useBudgets } from "@/hooks/use-budgets";

const STATUS_COLOR: Record<string, string> = {
  green: "bg-success",
  yellow: "bg-warning",
  red: "bg-destructive",
};

export function BudgetProgressWidget({ currency }: { currency: string }) {
  const today = new Date();
  const { data: budgets, isLoading } = useBudgets(today.getMonth() + 1, today.getFullYear());

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Budget Progress</CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/budgets">Manage</Link>
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : !budgets || budgets.length === 0 ? (
          <EmptyState
            title="No budgets set"
            description="Create a monthly budget to track your spending."
            action={
              <Button size="sm" asChild>
                <Link href="/budgets">Create budget</Link>
              </Button>
            }
          />
        ) : (
          budgets.slice(0, 5).map((budget) => (
            <div key={budget.id} className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{budget.name}</span>
                <span className="text-muted-foreground">
                  {formatCurrency(budget.spent, currency)} / {formatCurrency(budget.monthly_limit, currency)}
                </span>
              </div>
              <Progress
                value={Math.min(budget.percent_consumed, 100)}
                indicatorClassName={cn(STATUS_COLOR[budget.status])}
              />
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
