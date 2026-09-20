import { TrendingUp } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30 px-4 py-12">
      <div className="mb-8 flex items-center gap-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <TrendingUp className="h-5 w-5" />
        </div>
        <span className="text-2xl font-semibold">FinSight</span>
      </div>
      <div className="w-full max-w-sm">{children}</div>
      <p className="mt-8 max-w-sm text-center text-xs text-muted-foreground">
        Educational demo only. Uses synthetic or user-uploaded data — not connected to any real bank, and not
        financial advice.
      </p>
    </div>
  );
}
