"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/state-views";
import { formatCurrency } from "@/lib/utils";
import type { CategorySpend } from "@/types";

const COLORS = [
  "#6366f1", "#f97316", "#0ea5e9", "#ec4899", "#8b5cf6", "#ef4444",
  "#3b82f6", "#f59e0b", "#14b8a6", "#84cc16", "#06b6d4", "#a855f7",
  "#22c55e", "#64748b", "#94a3b8",
];

export function CategoryDonutChart({ data, currency }: { data: CategorySpend[]; currency: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Spending by Category</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <EmptyState title="No spending yet" description="Import transactions or add one to see this chart." />
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={data}
                dataKey="total"
                nameKey="category"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
              >
                {data.map((entry, index) => (
                  <Cell key={entry.category} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, name: string) => [formatCurrency(value, currency), name]}
                contentStyle={{ borderRadius: 8, border: "1px solid hsl(var(--border))" }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
