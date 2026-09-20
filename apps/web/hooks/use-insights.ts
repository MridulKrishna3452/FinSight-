"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  DailySpendPoint,
  ForecastResponse,
  InsightsDashboardResponse,
  MonthlySummaryItem,
  RecurringExpense,
  TopMerchant,
} from "@/types";

export function useDashboardInsights() {
  return useQuery({
    queryKey: ["insights", "dashboard"],
    queryFn: () => api.get<InsightsDashboardResponse>("/insights/dashboard"),
  });
}

export function useMonthlySummary(months = 6) {
  return useQuery({
    queryKey: ["insights", "monthly-summary", months],
    queryFn: () => api.get<MonthlySummaryItem[]>(`/insights/monthly-summary?months=${months}`),
  });
}

export function useDailySpending(days = 30) {
  return useQuery({
    queryKey: ["insights", "daily-spending", days],
    queryFn: () => api.get<DailySpendPoint[]>(`/insights/daily-spending?days=${days}`),
  });
}

export function useTopMerchants(limit = 10) {
  return useQuery({
    queryKey: ["insights", "top-merchants", limit],
    queryFn: () => api.get<TopMerchant[]>(`/insights/top-merchants?limit=${limit}`),
  });
}

export function useRecurringExpenses() {
  return useQuery({
    queryKey: ["insights", "recurring-expenses"],
    queryFn: () => api.get<RecurringExpense[]>("/insights/recurring-expenses"),
  });
}

export function useForecast() {
  return useQuery({
    queryKey: ["insights", "forecast"],
    queryFn: () => api.get<ForecastResponse>("/insights/forecast"),
  });
}
