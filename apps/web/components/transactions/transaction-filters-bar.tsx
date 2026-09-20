"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { CATEGORIES } from "@/types";
import type { TransactionFilters } from "@/hooks/use-transactions";

interface Props {
  filters: TransactionFilters;
  onChange: (filters: TransactionFilters) => void;
}

export function TransactionFiltersBar({ filters, onChange }: Props) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
      <div className="relative flex-1 sm:max-w-xs">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search merchant or description..."
          className="pl-8"
          defaultValue={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value, page: 1 })}
        />
      </div>

      <Select
        value={filters.category ?? "all"}
        onValueChange={(value) => onChange({ ...filters, category: value as TransactionFilters["category"], page: 1 })}
      >
        <SelectTrigger className="w-full sm:w-40">
          <SelectValue placeholder="Category" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All categories</SelectItem>
          {CATEGORIES.map((c) => (
            <SelectItem key={c} value={c}>
              {c}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.transaction_type ?? "all"}
        onValueChange={(value) =>
          onChange({ ...filters, transaction_type: value as TransactionFilters["transaction_type"], page: 1 })
        }
      >
        <SelectTrigger className="w-full sm:w-36">
          <SelectValue placeholder="Type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All types</SelectItem>
          <SelectItem value="income">Income</SelectItem>
          <SelectItem value="expense">Expense</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.is_suspicious === undefined ? "all" : filters.is_suspicious ? "suspicious" : "normal"}
        onValueChange={(value) =>
          onChange({
            ...filters,
            is_suspicious: value === "all" ? undefined : value === "suspicious",
            page: 1,
          })
        }
      >
        <SelectTrigger className="w-full sm:w-40">
          <SelectValue placeholder="Risk" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All transactions</SelectItem>
          <SelectItem value="suspicious">Suspicious only</SelectItem>
          <SelectItem value="normal">Normal only</SelectItem>
        </SelectContent>
      </Select>

      <div className="flex items-center gap-2">
        <Input
          type="date"
          value={filters.date_from ?? ""}
          onChange={(e) => onChange({ ...filters, date_from: e.target.value, page: 1 })}
          className="w-full sm:w-36"
        />
        <span className="text-sm text-muted-foreground">to</span>
        <Input
          type="date"
          value={filters.date_to ?? ""}
          onChange={(e) => onChange({ ...filters, date_to: e.target.value, page: 1 })}
          className="w-full sm:w-36"
        />
      </div>

      {(filters.search || filters.category !== "all" || filters.transaction_type !== "all" || filters.is_suspicious !== undefined || filters.date_from || filters.date_to) && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() =>
            onChange({
              page: 1,
              page_size: filters.page_size,
              sort_by: filters.sort_by,
              sort_dir: filters.sort_dir,
            })
          }
        >
          Clear filters
        </Button>
      )}
    </div>
  );
}
