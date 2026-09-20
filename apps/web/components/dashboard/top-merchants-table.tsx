import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CategoryBadge } from "@/components/shared/category-badge";
import { EmptyState } from "@/components/shared/state-views";
import { formatCurrency } from "@/lib/utils";
import type { TopMerchant } from "@/types";

export function TopMerchantsTable({ merchants, currency }: { merchants: TopMerchant[]; currency: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Merchants</CardTitle>
      </CardHeader>
      <CardContent>
        {merchants.length === 0 ? (
          <EmptyState title="No merchant data yet" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Merchant</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Transactions</TableHead>
                <TableHead className="text-right">Total Spent</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {merchants.map((m) => (
                <TableRow key={m.merchant_name}>
                  <TableCell className="font-medium">{m.merchant_name}</TableCell>
                  <TableCell>
                    <CategoryBadge category={m.category} />
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">{m.transaction_count}</TableCell>
                  <TableCell className="text-right font-medium">{formatCurrency(m.total, currency)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
