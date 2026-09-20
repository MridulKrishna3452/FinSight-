"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { AppShell } from "@/components/shared/app-shell";
import { Button } from "@/components/ui/button";
import { CardSkeletonGrid, EmptyState, ErrorState } from "@/components/shared/state-views";
import { BudgetCard } from "@/components/budgets/budget-card";
import { BudgetFormDialog } from "@/components/budgets/budget-form-dialog";
import { useAuth } from "@/lib/auth";
import { useBudgets } from "@/hooks/use-budgets";

export default function BudgetsPage() {
  const { user } = useAuth();
  const [dialogOpen, setDialogOpen] = useState(false);
  const today = new Date();
  const { data: budgets, isLoading, isError, refetch } = useBudgets(today.getMonth() + 1, today.getFullYear());
  const currency = user?.currency ?? "INR";

  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Budgets</h1>
          <p className="text-sm text-muted-foreground">
            {today.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4" />
          Create budget
        </Button>
      </div>

      {isLoading && <CardSkeletonGrid />}
      {isError && <ErrorState description="Could not load your budgets." onRetry={() => refetch()} />}

      {budgets && budgets.length === 0 && (
        <EmptyState
          title="No budgets yet"
          description="Create monthly budgets to keep your spending on track."
          action={<Button onClick={() => setDialogOpen(true)}>Create your first budget</Button>}
        />
      )}

      {budgets && budgets.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {budgets.map((budget) => (
            <BudgetCard key={budget.id} budget={budget} currency={currency} />
          ))}
        </div>
      )}

      <BudgetFormDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </AppShell>
  );
}
