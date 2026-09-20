import { z } from "zod";
import { CATEGORIES } from "@/types";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});
export type LoginFormValues = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  full_name: z.string().min(1, "Name is required").max(255),
  email: z.string().email("Enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .max(128),
});
export type RegisterFormValues = z.infer<typeof registerSchema>;

export const transactionFormSchema = z.object({
  transaction_date: z.string().min(1, "Date is required"),
  merchant_name: z.string().min(1, "Merchant is required").max(255),
  description: z.string().min(1, "Description is required").max(500),
  amount: z
    .string()
    .min(1, "Amount is required")
    .refine((v) => !Number.isNaN(parseFloat(v)) && parseFloat(v) > 0, "Enter a positive amount"),
  transaction_type: z.enum(["income", "expense"]),
  category: z.enum(CATEGORIES).optional(),
  payment_method: z.string().min(1).max(100).default("Other"),
  is_recurring: z.boolean().default(false),
});
export type TransactionFormValues = z.infer<typeof transactionFormSchema>;

export const budgetFormSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  category: z.enum(CATEGORIES).optional(),
  monthly_limit: z
    .string()
    .min(1, "Amount is required")
    .refine((v) => !Number.isNaN(parseFloat(v)) && parseFloat(v) > 0, "Enter a positive amount"),
  month: z.number().min(1).max(12),
  year: z.number().min(2000).max(2100),
});
export type BudgetFormValues = z.infer<typeof budgetFormSchema>;
