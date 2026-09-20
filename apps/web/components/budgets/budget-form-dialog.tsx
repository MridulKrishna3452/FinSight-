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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { budgetFormSchema, type BudgetFormValues } from "@/lib/schemas";
import { CATEGORIES } from "@/types";
import { useCreateBudget } from "@/hooks/use-budgets";
import { ApiError } from "@/lib/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function BudgetFormDialog({ open, onOpenChange }: Props) {
  const createMutation = useCreateBudget();
  const today = new Date();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<BudgetFormValues>({
    resolver: zodResolver(budgetFormSchema),
    defaultValues: {
      name: "",
      monthly_limit: "",
      month: today.getMonth() + 1,
      year: today.getFullYear(),
    },
  });

  useEffect(() => {
    if (open) {
      reset({ name: "", monthly_limit: "", month: today.getMonth() + 1, year: today.getFullYear() });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const category = watch("category");

  const onSubmit = async (values: BudgetFormValues) => {
    try {
      await createMutation.mutateAsync(values);
      toast.success("Budget created");
      onOpenChange(false);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not create budget";
      toast.error(message);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create budget</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="name">Budget name</Label>
            <Input id="name" placeholder="e.g. Groceries Budget" {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>

          <div className="space-y-1.5">
            <Label>Category (leave unset for overall budget)</Label>
            <Select
              value={category ?? "__overall__"}
              onValueChange={(v) => setValue("category", v === "__overall__" ? undefined : (v as BudgetFormValues["category"]))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__overall__">Overall monthly budget</SelectItem>
                {CATEGORIES.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="monthly_limit">Monthly limit</Label>
            <Input id="monthly_limit" type="number" step="0.01" {...register("monthly_limit")} />
            {errors.monthly_limit && <p className="text-xs text-destructive">{errors.monthly_limit.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Month</Label>
              <Select value={String(watch("month"))} onValueChange={(v) => setValue("month", Number(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MONTH_NAMES.map((name, idx) => (
                    <SelectItem key={name} value={String(idx + 1)}>
                      {name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="year">Year</Label>
              <Input
                id="year"
                type="number"
                {...register("year", { valueAsNumber: true })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create budget"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
