import Link from "next/link";
import { AlertCircle, CheckCircle2, Loader2, ShieldAlert } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { ImportJob } from "@/types";

const STATUS_LABEL: Record<string, string> = {
  queued: "Queued",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
};

export function ImportJobStatusCard({ job }: { job: ImportJob }) {
  const isPending = job.status === "queued" || job.status === "processing";
  const isFailed = job.status === "failed";

  return (
    <Card>
      <CardContent className="space-y-4 pt-6">
        <div className="flex items-center gap-3">
          {isPending && <Loader2 className="h-5 w-5 animate-spin text-primary" />}
          {job.status === "completed" && <CheckCircle2 className="h-5 w-5 text-success" />}
          {isFailed && <AlertCircle className="h-5 w-5 text-destructive" />}
          <div>
            <p className="font-medium">{job.filename}</p>
            <Badge variant={isFailed ? "destructive" : job.status === "completed" ? "success" : "secondary"}>
              {STATUS_LABEL[job.status]}
            </Badge>
          </div>
        </div>

        {isFailed && job.error_message && (
          <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{job.error_message}</p>
        )}

        {job.status === "completed" && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="Imported" value={job.imported_rows} />
            <Stat label="Duplicates skipped" value={job.duplicate_rows} />
            <Stat label="Failed rows" value={job.failed_rows} />
            <Stat
              label="Suspicious"
              value={job.suspicious_rows}
              icon={job.suspicious_rows > 0 ? <ShieldAlert className="h-3.5 w-3.5 text-destructive" /> : undefined}
            />
          </div>
        )}

        {job.status === "completed" && job.suspicious_rows > 0 && (
          <div className="flex items-center justify-between rounded-md bg-destructive/5 p-3">
            <p className="text-sm">
              {job.suspicious_rows} imported transaction{job.suspicious_rows === 1 ? "" : "s"} flagged as risk
              indicators.
            </p>
            <Button size="sm" variant="outline" asChild>
              <Link href="/alerts">View alerts</Link>
            </Button>
          </div>
        )}

        {job.status === "completed" && (
          <Button asChild className="w-full">
            <Link href="/transactions">View imported transactions</Link>
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function Stat({ label, value, icon }: { label: string; value: number; icon?: React.ReactNode }) {
  return (
    <div className="rounded-lg border p-3 text-center">
      <div className="flex items-center justify-center gap-1 text-xl font-bold">
        {icon}
        {value}
      </div>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
