"use client";

import { useState } from "react";
import { AlertTriangle, ArrowDown, ArrowUp, MoreHorizontal } from "lucide-react";
import { toast } from "sonner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CategoryBadge, TransactionTypeBadge } from "@/components/shared/category-badge";
import { EmptyState } from "@/components/shared/state-views";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useDeleteTransaction, type TransactionFilters } from "@/hooks/use-transactions";
import { ApiError } from "@/lib/api";
import type { Transaction } from "@/types";

interface Props {
  transactions: Transaction[];
  currency: string;
  filters: TransactionFilters;
  onSortChange: (filters: TransactionFilters) => void;
  onEdit: (transaction: Transaction) => void;
}

function SortHeader({
  label,
  column,
  filters,
  onSortChange,
}: {
  label: string;
  column: string;
  filters: TransactionFilters;
  onSortChange: (filters: TransactionFilters) => void;
}) {
  const isActive = filters.sort_by === column;
  const nextDir = isActive && filters.sort_dir === "desc" ? "asc" : "desc";

  return (
    <button
      className="flex items-center gap-1 hover:text-foreground"
      onClick={() => onSortChange({ ...filters, sort_by: column, sort_dir: nextDir })}
    >
      {label}
      {isActive &&
        (filters.sort_dir === "desc" ? <ArrowDown className="h-3 w-3" /> : <ArrowUp className="h-3 w-3" />)}
    </button>
  );
}

export function TransactionTable({ transactions, currency, filters, onSortChange, onEdit }: Props) {
  const [deleteTarget, setDeleteTarget] = useState<Transaction | null>(null);
  const deleteMutation = useDeleteTransaction();

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      toast.success("Transaction deleted");
      setDeleteTarget(null);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not delete transaction";
      toast.error(message);
    }
  };

  if (transactions.length === 0) {
    return <EmptyState title="No transactions found" description="Try adjusting your filters." />;
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <SortHeader label="Date" column="transaction_date" filters={filters} onSortChange={onSortChange} />
            </TableHead>
            <TableHead>
              <SortHeader label="Merchant" column="merchant_name" filters={filters} onSortChange={onSortChange} />
            </TableHead>
            <TableHead>Description</TableHead>
            <TableHead>
              <SortHeader label="Category" column="category" filters={filters} onSortChange={onSortChange} />
            </TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="text-right">
              <SortHeader label="Amount" column="amount" filters={filters} onSortChange={onSortChange} />
            </TableHead>
            <TableHead className="w-10" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.map((t) => (
            <TableRow key={t.id} className={t.is_suspicious ? "bg-destructive/5" : undefined}>
              <TableCell className="whitespace-nowrap text-muted-foreground">
                {formatDate(t.transaction_date)}
              </TableCell>
              <TableCell className="font-medium">
                <div className="flex items-center gap-1.5">
                  {t.is_suspicious && (
                    <span title={t.anomaly_explanation ?? "Flagged as suspicious"}>
                      <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
                    </span>
                  )}
                  {t.merchant_name}
                </div>
              </TableCell>
              <TableCell className="max-w-[220px] truncate text-muted-foreground">{t.description}</TableCell>
              <TableCell>
                <CategoryBadge category={t.category} />
              </TableCell>
              <TableCell>
                <TransactionTypeBadge type={t.transaction_type} />
              </TableCell>
              <TableCell
                className={`text-right font-medium whitespace-nowrap ${t.transaction_type === "income" ? "text-success" : ""}`}
              >
                {t.transaction_type === "income" ? "+" : "-"}
                {formatCurrency(t.amount, currency)}
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onEdit(t)}>Edit</DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive" onClick={() => setDeleteTarget(t)}>
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete transaction?</DialogTitle>
            <DialogDescription>
              This will permanently remove &quot;{deleteTarget?.description}&quot;.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
