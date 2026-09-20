"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ImportJob, ImportPreviewResponse } from "@/types";

export function usePreviewCsv() {
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.postForm<ImportPreviewResponse>("/imports/csv/preview", formData);
    },
  });
}

export function useUploadCsv() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.postForm<ImportJob>("/imports/csv", formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
  });
}

export function useImportJob(jobId: string | null, options?: { pollWhilePending?: boolean }) {
  return useQuery({
    queryKey: ["import-job", jobId],
    queryFn: () => api.get<ImportJob>(`/imports/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (query) => {
      if (!options?.pollWhilePending) return false;
      const status = query.state.data?.status;
      return status === "queued" || status === "processing" ? 1500 : false;
    },
  });
}
