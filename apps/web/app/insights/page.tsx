"use client";

import { AppShell } from "@/components/shared/app-shell";
import { CardSkeletonGrid } from "@/components/shared/state-views";
import { SummaryCards } from "@/components/dashboard/summary-cards";
import { CategoryDonutChart } from "@/components/dashboard/category-donut-chart";
import { MonthlyBarChart } from "@/components/dashboard/monthly-bar-chart";
import { DailyTrendChart } from "@/components/dashboard/daily-trend-chart";
import { ForecastChart } from "@/components/dashboard/forecast-chart";
import { TopMerchantsTable } from "@/components/dashboard/top-merchants-table";
import { RecurringExpensesList } from "@/components/dashboard/recurring-expenses-list";
import { useAuth } from "@/lib/auth";
import {
  useDashboardInsights,
  useMonthlySummary,
  useDailySpending,
  useForecast,
  useTopMerchants,
  useRecurringExpenses,
} from "@/hooks/use-insights";

export default function InsightsPage() {
  const { user } = useAuth();
  const currency = user?.currency ?? "INR";

  const dashboard = useDashboardInsights();
  const monthlySummary = useMonthlySummary(6);
  const dailySpending = useDailySpending(30);
  const forecast = useForecast();
  const topMerchants = useTopMerchants(8);
  const recurring = useRecurringExpenses();

  const isLoading =
    dashboard.isLoading || monthlySummary.isLoading || dailySpending.isLoading || forecast.isLoading;

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Insights</h1>
        <p className="text-sm text-muted-foreground">
          A deeper look at your spending patterns, trends, and forecast.
        </p>
      </div>

      {isLoading && <CardSkeletonGrid />}

      {dashboard.data && (
        <div className="space-y-6">
          <SummaryCards summary={dashboard.data.summary} currency={currency} />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <MonthlyBarChart data={monthlySummary.data ?? []} currency={currency} />
            <CategoryDonutChart data={dashboard.data.spending_by_category} currency={currency} />
          </div>

          <DailyTrendChart data={dailySpending.data ?? []} currency={currency} />

          {forecast.data && <ForecastChart forecast={forecast.data} currency={currency} />}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <TopMerchantsTable merchants={topMerchants.data ?? []} currency={currency} />
            <RecurringExpensesList items={recurring.data ?? []} currency={currency} />
          </div>
        </div>
      )}
    </AppShell>
  );
}
