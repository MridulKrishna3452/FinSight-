import path from "path";
import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test covering the core FinSight flow:
 *   1. Log in (demo account, seeded via `make seed` / `python -m app.seed.seed_demo_data`)
 *   2. Import sample transaction data via CSV (async Celery job)
 *   3. View the dashboard
 *   4. Create a budget
 *   5. View a suspicious-transaction alert
 *
 * Requires the full stack running locally (web on :3000, api on :8000,
 * Postgres, Redis, and a Celery worker) with demo data already seeded.
 */

const SAMPLE_CSV = path.join(__dirname, "..", "..", "..", "data", "sample_transactions.csv");

test("register/login -> import data -> dashboard -> budget -> suspicious alert", async ({ page }) => {
  // 1. Log in with the seeded demo account.
  await page.goto("/login");
  await page.getByLabel("Email").fill("demo@finsight.app");
  await page.getByLabel("Password").fill("Demo@12345");
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
  await expect(page.getByText("Welcome back")).toBeVisible();

  // 2. Import sample transaction data via CSV.
  await page.goto("/import");
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(SAMPLE_CSV);
  await expect(page.getByText(/Preview & confirm/i)).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: /Import \d+ rows/ }).click();
  await expect(page.getByText("Completed")).toBeVisible({ timeout: 30000 });

  // 3. View the dashboard.
  await page.goto("/dashboard");
  await expect(page.getByText("Balance").first()).toBeVisible();
  await expect(page.getByText("Monthly Income").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Savings Rate" })).toBeVisible();

  // 4. Create a budget.
  await page.goto("/budgets");
  await page.getByRole("button", { name: "Create budget" }).click();
  const budgetName = `E2E Test Budget ${Date.now()}`;
  await page.getByLabel("Budget name").fill(budgetName);
  await page.getByLabel("Monthly limit").fill("5000");
  await page.getByRole("button", { name: "Create budget" }).click();
  await expect(page.getByText(budgetName)).toBeVisible({ timeout: 10000 });

  // 5. View a suspicious-transaction alert.
  await page.goto("/alerts");
  await expect(page.getByText(/Suspicious transaction/i).first()).toBeVisible({ timeout: 10000 });
  await expect(page.getByText(/Risk indicator, not confirmed fraud/i).first()).toBeVisible();
});
