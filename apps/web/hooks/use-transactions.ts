"use client";

import { useMutation, useQuery, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import { api, buildQueryString } from "@/lib/api";
import type { Category, Page, Transaction, TransactionType } from "@/types";

export interface TransactionFilters {
  search?: string;
  category?: Category | "all";
  transaction_type?: TransactionType | "all";
  is_suspicious?: boolean;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

function normalizeFilters(filters: TransactionFilters): Record<string, string | number | boolean | undefined> {
  return {
    search: filters.search || undefined,
    category: filters.category && filters.category !== "all" ? filters.category : undefined,
    transaction_type:
      filters.transaction_type && filters.transaction_type !== "all" ? filters.transaction_type : undefined,
    is_suspicious: filters.is_suspicious,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    sort_by: filters.sort_by,
    sort_dir: filters.sort_dir,
    page: filters.page,
    page_size: filters.page_size,
  };
}

export function useTransactions(filters: TransactionFilters) {
  const qs = buildQueryString(normalizeFilters(filters));
  return useQuery({
    queryKey: ["transactions", filters],
    queryFn: () => api.get<Page<Transaction>>(`/transactions${qs}`),
    placeholderData: keepPreviousData,
  });
}

export interface TransactionInput {
  transaction_date: string;
  merchant_name: string;
  description: string;
  amount: string;
  transaction_type: TransactionType;
  category?: Category;
  payment_method: string;
  is_recurring: boolean;
}

export function useCreateTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TransactionInput) => api.post<Transaction>("/transactions", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["insights"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });
}

export function useUpdateTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<TransactionInput> }) =>
      api.patch<Transaction>(`/transactions/${id}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["insights"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

export function useDeleteTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete<void>(`/transactions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["insights"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

export async function exportTransactions(filters: TransactionFilters): Promise<void> {
  const qs = buildQueryString(normalizeFilters(filters));
  const blob = await api.getBlob(`/transactions/export${qs}`);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "finsight_transactions.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
