"use client";

import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CategoryBadge } from "@/components/shared/category-badge";
import { EmptyState } from "@/components/shared/state-views";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { useTransactions } from "@/hooks/use-transactions";

export function RecentTransactions({ currency }: { currency: string }) {
  const { data, isLoading } = useTransactions({ page: 1, page_size: 6, sort_by: "transaction_date", sort_dir: "desc" });
  const transactions = data?.items ?? [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Transactions</CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/transactions">View all</Link>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : transactions.length === 0 ? (
          <EmptyState
            title="No transactions yet"
            description="Import a CSV or add your first transaction to get started."
            action={
              <Button size="sm" asChild>
                <Link href="/import">Import transactions</Link>
              </Button>
            }
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Merchant</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-medium">{t.merchant_name}</TableCell>
                  <TableCell>
                    <CategoryBadge category={t.category} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">{formatDateShort(t.transaction_date)}</TableCell>
                  <TableCell
                    className={`text-right font-medium ${t.transaction_type === "income" ? "text-success" : ""}`}
                  >
                    {t.transaction_type === "income" ? "+" : "-"}
                    {formatCurrency(t.amount, currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
