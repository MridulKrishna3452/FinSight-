"use client";

import { useState } from "react";
import { Download, Plus } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/shared/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/shared/state-views";
import { TransactionFiltersBar } from "@/components/transactions/transaction-filters-bar";
import { TransactionTable } from "@/components/transactions/transaction-table";
import { TransactionPagination } from "@/components/transactions/transaction-pagination";
import { TransactionFormDialog } from "@/components/transactions/transaction-form-dialog";
import { useAuth } from "@/lib/auth";
import { useTransactions, exportTransactions, type TransactionFilters } from "@/hooks/use-transactions";
import type { Transaction } from "@/types";

const DEFAULT_FILTERS: TransactionFilters = {
  page: 1,
  page_size: 25,
  sort_by: "transaction_date",
  sort_dir: "desc",
};

export default function TransactionsPage() {
  const { user } = useAuth();
  const [filters, setFilters] = useState<TransactionFilters>(DEFAULT_FILTERS);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const { data, isLoading, isError, refetch } = useTransactions(filters);
  const currency = user?.currency ?? "INR";

  const handleAdd = () => {
    setEditingTransaction(null);
    setDialogOpen(true);
  };

  const handleEdit = (transaction: Transaction) => {
    setEditingTransaction(transaction);
    setDialogOpen(true);
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await exportTransactions(filters);
    } catch {
      toast.error("Could not export transactions");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <AppShell>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Transactions</h1>
          <p className="text-sm text-muted-foreground">
            {data ? `${data.total} transaction${data.total === 1 ? "" : "s"}` : "Loading..."}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport} disabled={isExporting}>
            <Download className="h-4 w-4" />
            {isExporting ? "Exporting..." : "Export CSV"}
          </Button>
          <Button onClick={handleAdd}>
            <Plus className="h-4 w-4" />
            Add transaction
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="mb-4">
            <TransactionFiltersBar filters={filters} onChange={setFilters} />
          </div>

          {isLoading && <LoadingState label="Loading transactions..." />}
          {isError && <ErrorState description="Could not load transactions." onRetry={() => refetch()} />}

          {data && (
            <>
              <TransactionTable
                transactions={data.items}
                currency={currency}
                filters={filters}
                onSortChange={setFilters}
                onEdit={handleEdit}
              />
              <TransactionPagination
                page={data.page}
                totalPages={data.total_pages}
                total={data.total}
                pageSize={data.page_size}
                onPageChange={(page) => setFilters({ ...filters, page })}
              />
            </>
          )}
        </CardContent>
      </Card>

      <TransactionFormDialog open={dialogOpen} onOpenChange={setDialogOpen} transaction={editingTransaction} />
    </AppShell>
  );
}
