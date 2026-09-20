"use client";

import Link from "next/link";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAlerts } from "@/hooks/use-alerts";
import { formatDateShort } from "@/lib/utils";

export function RiskAlertWidget() {
  const { data: alerts, isLoading } = useAlerts(true);
  const suspiciousAlerts = (alerts ?? []).filter((a) => a.alert_type === "suspicious_transaction").slice(0, 3);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-destructive" />
          Risk Alerts
        </CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/alerts">View all</Link>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : suspiciousAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-6 text-center">
            <ShieldCheck className="h-8 w-8 text-success" />
            <p className="text-sm text-muted-foreground">No suspicious activity detected.</p>
          </div>
        ) : (
          <ul className="space-y-3">
            {suspiciousAlerts.map((alert) => (
              <li key={alert.id} className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
                <p className="text-sm font-medium">{alert.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">{alert.message}</p>
                <p className="mt-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                  {formatDateShort(alert.created_at)}
                </p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
