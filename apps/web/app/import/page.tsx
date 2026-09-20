"use client";

import { useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/shared/app-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CsvDropzone } from "@/components/shared/csv-dropzone";
import { ImportPreviewTable } from "@/components/shared/import-preview-table";
import { ImportJobStatusCard } from "@/components/shared/import-job-status";
import { LoadingState } from "@/components/shared/state-views";
import { usePreviewCsv, useUploadCsv, useImportJob } from "@/hooks/use-imports";
import { ApiError } from "@/lib/api";
import type { ImportPreviewResponse } from "@/types";

type Step = "upload" | "preview" | "processing";

export default function ImportPage() {
  const [step, setStep] = useState<Step>("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const previewMutation = usePreviewCsv();
  const uploadMutation = useUploadCsv();
  const { data: job } = useImportJob(jobId, { pollWhilePending: true });

  const handleFileSelected = async (file: File) => {
    setSelectedFile(file);
    try {
      const result = await previewMutation.mutateAsync(file);
      setPreview(result);
      setStep("preview");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not read this CSV file";
      toast.error(message);
    }
  };

  const handleConfirm = async () => {
    if (!selectedFile) return;
    try {
      const result = await uploadMutation.mutateAsync(selectedFile);
      setJobId(result.id);
      setStep("processing");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Import failed to start";
      toast.error(message);
    }
  };

  const handleReset = () => {
    setStep("upload");
    setSelectedFile(null);
    setPreview(null);
    setJobId(null);
  };

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Import Transactions</h1>
        <p className="text-sm text-muted-foreground">
          Upload a CSV export from your bank or card statement. Processing happens asynchronously in the
          background.
        </p>
      </div>

      <div className="mx-auto max-w-3xl space-y-6">
        {step === "upload" && (
          <Card>
            <CardHeader>
              <CardTitle>1. Upload CSV</CardTitle>
              <CardDescription>
                Expected columns: date, description, amount, type, merchant, payment_method. Common alternative
                header names are auto-detected.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CsvDropzone onFileSelected={handleFileSelected} disabled={previewMutation.isPending} />
              {previewMutation.isPending && <LoadingState label="Reading file..." />}
            </CardContent>
          </Card>
        )}

        {step === "preview" && preview && (
          <Card>
            <CardHeader>
              <CardTitle>2. Preview &amp; confirm</CardTitle>
              <CardDescription>
                Review the first rows below. Categorization and fraud-risk scoring happen automatically after you
                confirm.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ImportPreviewTable preview={preview} />
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={handleReset}>
                  Choose a different file
                </Button>
                <Button onClick={handleConfirm} disabled={uploadMutation.isPending}>
                  {uploadMutation.isPending ? "Starting import..." : `Import ${preview.total_rows} rows`}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {step === "processing" && (
          <Card>
            <CardHeader>
              <CardTitle>3. Import status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {job ? <ImportJobStatusCard job={job} /> : <LoadingState label="Starting import..." />}
              {job && (job.status === "completed" || job.status === "failed") && (
                <Button variant="outline" onClick={handleReset} className="w-full">
                  Import another file
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
