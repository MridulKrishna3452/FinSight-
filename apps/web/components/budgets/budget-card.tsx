"use client";

import { useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { formatCurrency, formatPercent, cn } from "@/lib/utils";
import { useDeleteBudget } from "@/hooks/use-budgets";
import { ApiError } from "@/lib/api";
import type { BudgetProgress } from "@/types";

const STATUS_CONFIG = {
  green: { bar: "bg-success", badge: "success" as const },
  yellow: { bar: "bg-warning", badge: "warning" as const },
  red: { bar: "bg-destructive", badge: "destructive" as const },
} satisfies Record<string, { bar: string; badge: "success" | "warning" | "destructive" }>;

export function BudgetCard({ budget, currency }: { budget: BudgetProgress; currency: string }) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const deleteMutation = useDeleteBudget();
  const config = STATUS_CONFIG[budget.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.green;

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(budget.id);
      toast.success("Budget deleted");
      setConfirmOpen(false);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not delete budget";
      toast.error(message);
    }
  };

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
          <div>
            <CardTitle className="text-base">{budget.name}</CardTitle>
            <p className="text-xs text-muted-foreground">{budget.category ?? "Overall"}</p>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setConfirmOpen(true)}>
            <Trash2 className="h-4 w-4 text-muted-foreground" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-baseline justify-between">
            <span className="text-xl font-bold">{formatCurrency(budget.spent, currency)}</span>
            <span className="text-sm text-muted-foreground">
              of {formatCurrency(budget.monthly_limit, currency)}
            </span>
          </div>
          <Progress value={Math.min(budget.percent_consumed, 100)} indicatorClassName={cn(config.bar)} />
          <div className="flex items-center justify-between text-xs">
            <Badge variant={config.badge}>{formatPercent(budget.percent_consumed)} used</Badge>
            <span className="text-muted-foreground">
              {Number(budget.remaining) >= 0
                ? `${formatCurrency(budget.remaining, currency)} remaining`
                : `${formatCurrency(Math.abs(Number(budget.remaining)), currency)} over budget`}
            </span>
          </div>
        </CardContent>
      </Card>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete budget?</DialogTitle>
            <DialogDescription>
              This will remove &quot;{budget.name}&quot;. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
