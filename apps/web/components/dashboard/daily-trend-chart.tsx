"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/state-views";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import type { DailySpendPoint } from "@/types";

export function DailyTrendChart({ data, currency }: { data: DailySpendPoint[]; currency: string }) {
  const chartData = data.map((d) => ({ date: formatDateShort(d.date), amount: Number(d.amount) }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Daily Spending Trend</CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <EmptyState title="No data yet" description="Import transactions to see your spending trend." />
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => formatCurrency(v, currency)} width={80} />
              <Tooltip formatter={(value: number) => formatCurrency(value, currency)} />
              <Line type="monotone" dataKey="amount" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
