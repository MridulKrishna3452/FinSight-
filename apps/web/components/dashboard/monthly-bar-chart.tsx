"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/state-views";
import { formatCurrency } from "@/lib/utils";
import type { MonthlySummaryItem } from "@/types";

export function MonthlyBarChart({ data, currency }: { data: MonthlySummaryItem[]; currency: string }) {
  const chartData = data.map((d) => ({
    month: new Date(`${d.month}-01`).toLocaleDateString("en-US", { month: "short", year: "2-digit" }),
    Income: Number(d.income),
    Expense: Number(d.expense),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Income vs. Expense</CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <EmptyState title="No data yet" description="Import transactions to see monthly trends." />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => formatCurrency(v, currency)} width={80} />
              <Tooltip formatter={(value: number) => formatCurrency(value, currency)} />
              <Legend />
              <Bar dataKey="Income" fill="hsl(var(--success))" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Expense" fill="hsl(var(--destructive))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
