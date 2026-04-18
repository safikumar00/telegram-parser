import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ChannelStatsWithMeta } from "@/types";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export function ChannelPerformance({
  stats,
}: {
  stats: ChannelStatsWithMeta[];
}) {
  if (stats.length === 0) {
    return (
      <Card data-testid="channel-performance-card" className="overflow-hidden">
        <CardHeader className="border-b border-border/50 pb-5">
          <CardTitle className="text-lg">Channel performance</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            Win-rate × avg profit across evaluated signals. Updates after every
            cron tick.
          </p>
        </CardHeader>
        <CardContent>
          <div
            data-testid="channel-performance-empty"
            className="flex flex-col items-start gap-2 py-4 text-sm"
          >
            <div className="font-medium">Nothing evaluated yet</div>
            <div className="max-w-md text-muted-foreground">
              Channels appear here once the processor has closed at least one
              signal. Trigger a run manually with{" "}
              <code className="font-mono text-xs">GET /api/cron/process</code>.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="channel-performance-card" className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between gap-4 border-b border-border/50 pb-5">
        <div>
          <CardTitle className="text-lg">Channel performance</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            Win-rate × avg profit across evaluated signals.
          </p>
        </div>
        <Badge
          variant="outline"
          className="rounded-full border-border/70 bg-white/70 font-mono text-[10px] uppercase tracking-[0.18em]"
        >
          {stats.length} channel{stats.length === 1 ? "" : "s"}
        </Badge>
      </CardHeader>
      <CardContent className="grid gap-4 p-6 md:grid-cols-2 xl:grid-cols-3">
        {stats.map((s) => (
          <ChannelCard key={s.channel_id} s={s} />
        ))}
      </CardContent>
    </Card>
  );
}

function ChannelCard({ s }: { s: ChannelStatsWithMeta }) {
  const profitPositive = s.avg_profit > 0;
  const profitNegative = s.avg_profit < 0;
  const Icon = profitPositive
    ? TrendingUp
    : profitNegative
    ? TrendingDown
    : Minus;
  const profitColor = profitPositive
    ? "text-emerald-600"
    : profitNegative
    ? "text-rose-600"
    : "text-muted-foreground";

  return (
    <div
      data-testid={`channel-perf-${s.channel_id}`}
      className="relative rounded-2xl border border-border/60 bg-white/70 p-5 backdrop-blur transition-all hover:-translate-y-0.5 hover:shadow-[0_16px_36px_-16px_rgba(60,60,140,0.18)]"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-foreground">
            {s.channel_name ?? "Unknown channel"}
          </div>
          <div className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            {s.channel_telegram_id ?? "—"}
          </div>
        </div>
        <div
          className={`flex h-9 w-9 flex-none items-center justify-center rounded-xl border border-border/70 bg-white/80 ${profitColor}`}
        >
          <Icon className="h-4 w-4" strokeWidth={1.75} />
        </div>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3">
        <Metric
          label="Win rate"
          value={`${s.win_rate.toFixed(2)}%`}
          tone={s.win_rate >= 50 ? "good" : s.win_rate > 0 ? "warn" : "muted"}
        />
        <Metric
          label="Avg profit"
          value={`${s.avg_profit > 0 ? "+" : ""}${s.avg_profit.toFixed(2)}%`}
          tone={profitPositive ? "good" : profitNegative ? "bad" : "muted"}
        />
        <Metric label="Trades" value={String(s.total_trades)} />
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  tone = "muted",
}: {
  label: string;
  value: string;
  tone?: "good" | "bad" | "warn" | "muted";
}) {
  const toneClass =
    tone === "good"
      ? "text-emerald-600"
      : tone === "bad"
      ? "text-rose-600"
      : tone === "warn"
      ? "text-amber-600"
      : "text-foreground";
  return (
    <div className="min-w-0">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </div>
      <div
        className={`mt-1 truncate text-lg font-medium tracking-tight ${toneClass}`}
      >
        {value}
      </div>
    </div>
  );
}
