"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/state-views";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import type { ForecastResponse } from "@/types";

export function ForecastChart({ forecast, currency }: { forecast: ForecastResponse; currency: string }) {
  const chartData = forecast.points.map((p) => ({
    date: formatDateShort(p.date),
    amount: Number(p.predicted_amount),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>30-Day Expense Forecast</CardTitle>
        <CardDescription>{forecast.disclaimer}</CardDescription>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <EmptyState title="Not enough data" description="Import more transaction history to generate a forecast." />
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => formatCurrency(v, currency)} width={80} />
              <Tooltip formatter={(value: number) => formatCurrency(value, currency)} />
              <Area
                type="monotone"
                dataKey="amount"
                stroke="hsl(var(--primary))"
                fill="url(#forecastFill)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
        <p className="mt-3 text-xs text-muted-foreground">
          Historical daily average: {formatCurrency(forecast.historical_daily_average, currency)}
        </p>
      </CardContent>
    </Card>
  );
}
