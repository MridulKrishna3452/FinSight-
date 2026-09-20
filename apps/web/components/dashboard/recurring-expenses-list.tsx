import { Repeat } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CategoryBadge } from "@/components/shared/category-badge";
import { EmptyState } from "@/components/shared/state-views";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import type { RecurringExpense } from "@/types";

export function RecurringExpensesList({ items, currency }: { items: RecurringExpense[]; currency: string }) {
  const monthlyTotal = items.reduce((sum, item) => sum + Number(item.average_amount), 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Repeat className="h-4 w-4 text-primary" />
          Recurring Expenses
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyState
            title="No recurring expenses found"
            description="Mark transactions as recurring to track subscriptions here."
          />
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div key={`${item.merchant_name}-${item.category}`} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="text-sm font-medium">{item.merchant_name}</p>
                  <div className="mt-1 flex items-center gap-2">
                    <CategoryBadge category={item.category} />
                    <span className="text-xs text-muted-foreground">
                      Last charged {formatDateShort(item.last_date)}
                    </span>
                  </div>
                </div>
                <span className="font-medium">{formatCurrency(item.average_amount, currency)}/mo</span>
              </div>
            ))}
            <div className="flex items-center justify-between border-t pt-3 text-sm font-medium">
              <span>Total recurring</span>
              <span>{formatCurrency(monthlyTotal, currency)}/mo</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
