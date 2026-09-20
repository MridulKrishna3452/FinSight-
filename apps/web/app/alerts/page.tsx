"use client";

import { useState } from "react";
import { AlertTriangle, Check, ShieldAlert, Wallet } from "lucide-react";
import { AppShell } from "@/components/shared/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState, ErrorState, LoadingState } from "@/components/shared/state-views";
import { cn, formatDate } from "@/lib/utils";
import { useAlerts, useMarkAlertRead } from "@/hooks/use-alerts";
import type { Alert } from "@/types";

const SEVERITY_STYLES: Record<string, string> = {
  info: "border-border",
  warning: "border-warning/50 bg-warning/5",
  critical: "border-destructive/50 bg-destructive/5",
};

function AlertIcon({ alert }: { alert: Alert }) {
  if (alert.alert_type === "suspicious_transaction") {
    return <ShieldAlert className="h-4 w-4 text-destructive" />;
  }
  return <Wallet className="h-4 w-4 text-warning" />;
}

export default function AlertsPage() {
  const [filter, setFilter] = useState<"all" | "unread">("all");
  const { data: alerts, isLoading, isError, refetch } = useAlerts(filter === "unread");
  const markRead = useMarkAlertRead();

  return (
    <AppShell>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Alerts</h1>
          <p className="text-sm text-muted-foreground">
            Suspicious-transaction and budget alerts. These are risk indicators, not confirmed fraud.
          </p>
        </div>
        <Tabs value={filter} onValueChange={(v) => setFilter(v as "all" | "unread")}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="unread">Unread</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {isLoading && <LoadingState label="Loading alerts..." />}
      {isError && <ErrorState description="Could not load alerts." onRetry={() => refetch()} />}

      {alerts && alerts.length === 0 && (
        <EmptyState
          icon={AlertTriangle}
          title={filter === "unread" ? "No unread alerts" : "No alerts yet"}
          description="Suspicious transactions and budget thresholds will show up here."
        />
      )}

      {alerts && alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <Card key={alert.id} className={cn(SEVERITY_STYLES[alert.severity])}>
              <CardContent className="flex items-start justify-between gap-4 py-4">
                <div className="flex items-start gap-3">
                  <AlertIcon alert={alert} />
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{alert.title}</p>
                      {!alert.is_read && (
                        <Badge variant="secondary" className="text-[10px]">
                          New
                        </Badge>
                      )}
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{alert.message}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{formatDate(alert.created_at)}</p>
                  </div>
                </div>
                {!alert.is_read && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => markRead.mutate(alert.id)}
                    disabled={markRead.isPending}
                  >
                    <Check className="h-4 w-4" />
                    Mark read
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}
