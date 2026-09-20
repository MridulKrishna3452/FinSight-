import { AlertTriangle, Info, Sparkles, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { InsightCard as InsightCardType } from "@/types";

const SEVERITY_STYLES = {
  info: { icon: Info, className: "border-border bg-muted/40 text-foreground" },
  warning: { icon: AlertTriangle, className: "border-warning/40 bg-warning/10 text-foreground" },
  positive: { icon: TrendingUp, className: "border-success/40 bg-success/10 text-foreground" },
} satisfies Record<string, { icon: typeof Info; className: string }>;

export function InsightCards({ cards }: { cards: InsightCardType[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          Latest Insights
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {cards.map((card) => {
          const style =
            SEVERITY_STYLES[card.severity as keyof typeof SEVERITY_STYLES] ?? SEVERITY_STYLES.info;
          const Icon = style.icon;
          return (
            <div key={card.id} className={cn("flex items-start gap-3 rounded-lg border p-3", style.className)}>
              <Icon className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="text-sm font-medium">{card.title}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{card.message}</p>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
