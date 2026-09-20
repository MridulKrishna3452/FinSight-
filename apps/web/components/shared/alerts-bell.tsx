"use client";

import Link from "next/link";
import { Bell } from "lucide-react";
import { useAlerts } from "@/hooks/use-alerts";
import { Button } from "@/components/ui/button";

export function AlertsBell() {
  const { data: alerts } = useAlerts(true);
  const unreadCount = alerts?.length ?? 0;

  return (
    <Button variant="ghost" size="icon" className="relative" aria-label="Alerts" asChild>
      <Link href="/alerts">
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </Link>
    </Button>
  );
}
