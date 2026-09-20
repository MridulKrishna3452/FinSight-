"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { transactionFormSchema, type TransactionFormValues } from "@/lib/schemas";
import { CATEGORIES } from "@/types";
import type { Transaction } from "@/types";
import { useCreateTransaction, useUpdateTransaction } from "@/hooks/use-transactions";
import { ApiError } from "@/lib/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  transaction?: Transaction | null;
}

const PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash", "Bank Transfer", "Other"];

export function TransactionFormDialog({ open, onOpenChange, transaction }: Props) {
  const isEditing = !!transaction;
  const createMutation = useCreateTransaction();
  const updateMutation = useUpdateTransaction();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TransactionFormValues>({
    resolver: zodResolver(transactionFormSchema),
    defaultValues: {
      transaction_date: new Date().toISOString().slice(0, 10),
      merchant_name: "",
      description: "",
      amount: "",
      transaction_type: "expense",
      payment_method: "UPI",
      is_recurring: false,
    },
  });

  useEffect(() => {
    if (transaction) {
      reset({
        transaction_date: transaction.transaction_date,
        merchant_name: transaction.merchant_name,
        description: transaction.description,
        amount: transaction.amount,
        transaction_type: transaction.transaction_type,
        category: transaction.category,
        payment_method: transaction.payment_method,
        is_recurring: transaction.is_recurring,
      });
    } else if (open) {
      reset({
        transaction_date: new Date().toISOString().slice(0, 10),
        merchant_name: "",
        description: "",
        amount: "",
        transaction_type: "expense",
        payment_method: "UPI",
        is_recurring: false,
      });
    }
  }, [transaction, open, reset]);

  const transactionType = watch("transaction_type");
  const category = watch("category");
  const isRecurring = watch("is_recurring");

  const onSubmit = async (values: TransactionFormValues) => {
    try {
      if (isEditing && transaction) {
        await updateMutation.mutateAsync({ id: transaction.id, input: values });
        toast.success("Transaction updated");
      } else {
        await createMutation.mutateAsync(values);
        toast.success("Transaction added");
      }
      onOpenChange(false);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not save transaction";
      toast.error(message);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit transaction" : "Add transaction"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="transaction_date">Date</Label>
              <Input id="transaction_date" type="date" {...register("transaction_date")} />
              {errors.transaction_date && <p className="text-xs text-destructive">{errors.transaction_date.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="amount">Amount</Label>
              <Input id="amount" type="number" step="0.01" {...register("amount")} />
              {errors.amount && <p className="text-xs text-destructive">{errors.amount.message}</p>}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="merchant_name">Merchant</Label>
            <Input id="merchant_name" {...register("merchant_name")} />
            {errors.merchant_name && <p className="text-xs text-destructive">{errors.merchant_name.message}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="description">Description</Label>
            <Input id="description" {...register("description")} />
            {errors.description && <p className="text-xs text-destructive">{errors.description.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Type</Label>
              <Select value={transactionType} onValueChange={(v) => setValue("transaction_type", v as "income" | "expense")}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="expense">Expense</SelectItem>
                  <SelectItem value="income">Income</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Category (optional — auto-detected)</Label>
              <Select value={category ?? "__auto__"} onValueChange={(v) => setValue("category", v === "__auto__" ? undefined : (v as TransactionFormValues["category"]))}>
                <SelectTrigger>
                  <SelectValue placeholder="Auto-detect" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__auto__">Auto-detect</SelectItem>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Payment method</Label>
            <Select
              value={watch("payment_method")}
              onValueChange={(v) => setValue("payment_method", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PAYMENT_METHODS.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Checkbox
              id="is_recurring"
              checked={isRecurring}
              onCheckedChange={(checked) => setValue("is_recurring", checked === true)}
            />
            <Label htmlFor="is_recurring" className="font-normal">
              This is a recurring transaction (e.g. subscription, rent)
            </Label>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : isEditing ? "Save changes" : "Add transaction"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
