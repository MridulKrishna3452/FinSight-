"use client";

import Link from "next/link";
import { Upload } from "lucide-react";
import { AppShell } from "@/components/shared/app-shell";
import { Button } from "@/components/ui/button";
import { CardSkeletonGrid, ErrorState } from "@/components/shared/state-views";
import { SummaryCards } from "@/components/dashboard/summary-cards";
import { CategoryDonutChart } from "@/components/dashboard/category-donut-chart";
import { RecentTransactions } from "@/components/dashboard/recent-transactions";
import { BudgetProgressWidget } from "@/components/dashboard/budget-progress-widget";
import { RiskAlertWidget } from "@/components/dashboard/risk-alert-widget";
import { InsightCards } from "@/components/dashboard/insight-cards";
import { useAuth } from "@/lib/auth";
import { useDashboardInsights } from "@/hooks/use-insights";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, isLoading, isError, refetch } = useDashboardInsights();
  const currency = user?.currency ?? "INR";

  return (
    <AppShell>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Welcome back{user ? `, ${user.full_name.split(" ")[0]}` : ""}</h1>
          <p className="text-sm text-muted-foreground">Here&apos;s what&apos;s happening with your money.</p>
        </div>
        <Button asChild>
          <Link href="/import">
            <Upload className="h-4 w-4" />
            Import transactions
          </Link>
        </Button>
      </div>

      {isLoading && <CardSkeletonGrid />}
      {isError && <ErrorState description="Could not load your dashboard." onRetry={() => refetch()} />}

      {data && (
        <div className="space-y-6">
          <SummaryCards summary={data.summary} currency={currency} />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <RecentTransactions currency={currency} />
            </div>
            <RiskAlertWidget />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <CategoryDonutChart data={data.spending_by_category} currency={currency} />
            <BudgetProgressWidget currency={currency} />
            <InsightCards cards={data.insight_cards} />
          </div>
        </div>
      )}
    </AppShell>
  );
}
