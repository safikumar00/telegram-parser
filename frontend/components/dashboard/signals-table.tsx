import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatPrice, formatRelativeTime } from "@/lib/utils";
import type { SignalWithChannel } from "@/types";

export function SignalsTable({ signals }: { signals: SignalWithChannel[] }) {
  return (
    <div data-testid="signals-table-wrapper">
      <Table data-testid="signals-table">
        <TableHeader>
          <TableRow>
            <TableHead className="pl-6">Pair</TableHead>
            <TableHead>Entry</TableHead>
            <TableHead>SL</TableHead>
            <TableHead>TP</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Channel</TableHead>
            <TableHead className="pr-6 text-right">Ingested</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {signals.map((s) => (
            <TableRow
              key={s.id}
              data-testid={`signal-row-${s.id}`}
              className="font-mono text-[13px]"
            >
              <TableCell className="pl-6 font-medium text-foreground">
                {s.pair ?? "—"}
              </TableCell>
              <TableCell>{formatPrice(s.entry)}</TableCell>
              <TableCell className="text-rose-600">
                {formatPrice(s.stop_loss)}
              </TableCell>
              <TableCell className="text-emerald-600">
                {formatPrice(s.take_profit)}
              </TableCell>
              <TableCell>
                <Badge
                  variant={statusVariant(s.status)}
                  className="rounded-full font-sans text-[10px] uppercase tracking-wider"
                >
                  {s.status}
                </Badge>
              </TableCell>
              <TableCell className="font-sans text-sm text-muted-foreground">
                {s.channel?.name ?? "—"}
              </TableCell>
              <TableCell className="pr-6 text-right font-sans text-xs text-muted-foreground">
                {formatRelativeTime(s.created_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function statusVariant(
  status: string,
): "success" | "warning" | "info" | "secondary" {
  switch (status) {
    case "filled":
    case "won":
      return "success";
    case "stopped":
    case "lost":
      return "warning";
    case "active":
      return "info";
    default:
      return "secondary";
  }
}
