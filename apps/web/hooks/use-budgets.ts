"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { BudgetProgress, Category } from "@/types";

export function useBudgets(month?: number, year?: number) {
  const qs = month && year ? `?month=${month}&year=${year}` : "";
  return useQuery({
    queryKey: ["budgets", { month, year }],
    queryFn: () => api.get<BudgetProgress[]>(`/budgets${qs}`),
  });
}

export interface BudgetInput {
  name: string;
  category?: Category;
  monthly_limit: string;
  month: number;
  year: number;
}

export function useCreateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: BudgetInput) => api.post<BudgetProgress>("/budgets", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

export function useUpdateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name, monthly_limit }: { id: string; name?: string; monthly_limit?: string }) =>
      api.patch<BudgetProgress>(`/budgets/${id}`, { name, monthly_limit }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

export function useDeleteBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete<void>(`/budgets/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}
