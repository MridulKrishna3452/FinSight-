import { AlertCircle, CheckCircle2 } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ImportPreviewResponse } from "@/types";

export function ImportPreviewTable({ preview }: { preview: ImportPreviewResponse }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <p className="text-muted-foreground">
          Showing first {preview.preview_rows.length} of {preview.total_rows} rows
        </p>
      </div>
      <div className="overflow-hidden rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10" />
              <TableHead>Date</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Merchant</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Payment Method</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {preview.preview_rows.map((row) => (
              <TableRow key={row.row_number} className={!row.valid ? "bg-destructive/5" : undefined}>
                <TableCell>
                  {row.valid ? (
                    <CheckCircle2 className="h-4 w-4 text-success" />
                  ) : (
                    <span title={row.errors.join(", ")}>
                      <AlertCircle className="h-4 w-4 text-destructive" />
                    </span>
                  )}
                </TableCell>
                <TableCell>{row.date ?? "—"}</TableCell>
                <TableCell className="max-w-[180px] truncate">{row.description ?? "—"}</TableCell>
                <TableCell>{row.merchant ?? "—"}</TableCell>
                <TableCell>{row.amount ?? "—"}</TableCell>
                <TableCell>{row.type ?? "auto"}</TableCell>
                <TableCell>{row.payment_method ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
