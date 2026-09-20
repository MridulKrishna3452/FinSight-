"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Alert } from "@/types";

export function useAlerts(unreadOnly = false) {
  return useQuery({
    queryKey: ["alerts", { unreadOnly }],
    queryFn: () => api.get<Alert[]>(`/alerts${unreadOnly ? "?unread_only=true" : ""}`),
  });
}

export function useMarkAlertRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) => api.patch<Alert>(`/alerts/${alertId}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });
}
